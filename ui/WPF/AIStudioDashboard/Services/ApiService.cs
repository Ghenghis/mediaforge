using System.Net.Http;
using Newtonsoft.Json;
using AIStudioDashboard.Models;

namespace AIStudioDashboard.Services;

public interface IApiService
{
    Task<SystemHealth?> GetSystemHealthAsync();
    Task<VideoStats?> GetVideoStatsAsync();
    Task<List<FrameAnalysis>?> GetRecentFramesAsync();
    Task<List<ModelVersion>?> GetModelVersionsAsync();
    Task<TrainingProgress?> GetTrainingProgressAsync();
    Task StartFilteringAsync();
    Task PauseFilteringAsync();
    Task StopFilteringAsync();
}

public class ApiService : IApiService
{
    private readonly HttpClient _httpClient;
    
    // API Endpoints - MediaForge Services
    private const string GatewayUrl = "http://localhost:8300";
    private const string RatingStudioUrl = "http://localhost:8196";
    private const string OrchestratorUrl = "http://localhost:8210";
    private const string DatasetBuilderUrl = "http://localhost:8211";
    private const string LoraTrainingUrl = "http://localhost:8230";
    private const string LearningBrainUrl = "http://localhost:8225";
    
    // Unified WPF API (single entry point)
    private const string UnifiedApiUrl = "http://localhost:8190";
    
    // External Services
    private const string LMStudioUrl = "http://localhost:1234/v1";
    private const string OllamaUrl = "http://localhost:11434";
    private const string ComfyUIUrl = "http://localhost:8188";
    
    public ApiService()
    {
        _httpClient = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(5)
        };
    }
    
    public async Task<SystemHealth?> GetSystemHealthAsync()
    {
        var health = new SystemHealth();
        
        // Check LM Studio
        try
        {
            var response = await _httpClient.GetAsync($"{LMStudioUrl}/models");
            health.LMStudioOnline = response.IsSuccessStatusCode;
            
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                var models = JsonConvert.DeserializeObject<dynamic>(content);
                if (models?.data != null && models.data.Count > 0)
                {
                    health.CurrentModel = models.data[0].id?.ToString() ?? "Unknown";
                }
            }
        }
        catch
        {
            health.LMStudioOnline = false;
        }
        
        // Check Ollama
        try
        {
            var response = await _httpClient.GetAsync($"{OllamaUrl}/api/tags");
            health.OllamaOnline = response.IsSuccessStatusCode;
        }
        catch
        {
            health.OllamaOnline = false;
        }
        
        // Check Rating Studio
        try
        {
            var response = await _httpClient.GetAsync($"{RatingStudioUrl}/api/stats");
            health.RatingStudioOnline = response.IsSuccessStatusCode;
        }
        catch
        {
            health.RatingStudioOnline = false;
        }
        
        // Check Orchestrator
        try
        {
            var response = await _httpClient.GetAsync($"{OrchestratorUrl}/api/orchestrator/status");
            health.OrchestratorOnline = response.IsSuccessStatusCode;
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                var status = JsonConvert.DeserializeObject<dynamic>(content);
                health.OrchestratorState = status?.state?.ToString() ?? "unknown";
            }
        }
        catch
        {
            health.OrchestratorOnline = false;
        }
        
        // Check ComfyUI
        try
        {
            var response = await _httpClient.GetAsync($"{ComfyUIUrl}/system_stats");
            health.ComfyUIOnline = response.IsSuccessStatusCode;
        }
        catch
        {
            health.ComfyUIOnline = false;
        }
        
        // Get GPU/Memory stats (would need native interop or PowerShell)
        health.GpuUsage = await GetGpuUsageAsync();
        health.MemoryUsageGB = await GetMemoryUsageAsync();
        health.MemoryTotalGB = 16; // Hardcoded for now
        
        health.LastUpdate = DateTime.Now;
        
        return health;
    }
    
    private async Task<double> GetGpuUsageAsync()
    {
        try
        {
            // Simple check using nvidia-smi (if available)
            var psi = new System.Diagnostics.ProcessStartInfo
            {
                FileName = "nvidia-smi",
                Arguments = "--query-gpu=utilization.gpu --format=csv,noheader,nounits",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                CreateNoWindow = true
            };
            
            using var process = System.Diagnostics.Process.Start(psi);
            if (process != null)
            {
                var output = await process.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();
                
                if (double.TryParse(output.Trim(), out var usage))
                    return usage;
            }
        }
        catch
        {
            // nvidia-smi not available
        }
        
        return 0;
    }
    
    private async Task<double> GetMemoryUsageAsync()
    {
        try
        {
            var psi = new System.Diagnostics.ProcessStartInfo
            {
                FileName = "nvidia-smi",
                Arguments = "--query-gpu=memory.used --format=csv,noheader,nounits",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                CreateNoWindow = true
            };
            
            using var process = System.Diagnostics.Process.Start(psi);
            if (process != null)
            {
                var output = await process.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();
                
                if (double.TryParse(output.Trim(), out var usage))
                    return usage / 1024.0; // Convert MB to GB
            }
        }
        catch
        {
            // nvidia-smi not available
        }
        
        return 0;
    }
    
    public async Task<VideoStats?> GetVideoStatsAsync()
    {
        try
        {
            // Get stats from Rating Studio
            var response = await _httpClient.GetAsync($"{RatingStudioUrl}/api/stats");
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                var data = JsonConvert.DeserializeObject<dynamic>(content);
                
                return new VideoStats
                {
                    TotalVideos = data?.total ?? 0,
                    ProcessedVideos = data?.rated ?? 0,
                    ApprovedVideos = data?.high7 ?? 0,
                    RejectedVideos = (data?.rated ?? 0) - (data?.high7 ?? 0)
                };
            }
        }
        catch { }
        
        return null;
    }
    
    public async Task<List<FrameAnalysis>?> GetRecentFramesAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{RatingStudioUrl}/api/images?filter=high&limit=20");
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<List<FrameAnalysis>>(content);
            }
        }
        catch { }
        
        return null;
    }
    
    public async Task<List<ModelVersion>?> GetModelVersionsAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{OrchestratorUrl}/api/orchestrator/history");
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<List<ModelVersion>>(content);
            }
        }
        catch { }
        
        return null;
    }
    
    public async Task<TrainingProgress?> GetTrainingProgressAsync()
    {
        try
        {
            // Check LoRA Training service for active training
            var response = await _httpClient.GetAsync($"{LoraTrainingUrl}/api/status");
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                var data = JsonConvert.DeserializeObject<dynamic>(content);
                
                if (data?.is_training == true)
                {
                    var job = data?.current_job;
                    return new TrainingProgress
                    {
                        ModelName = job?.name?.ToString() ?? "Training",
                        CurrentStep = (int)(job?.current_step ?? 0),
                        TotalSteps = (int)(job?.steps ?? 0),
                        CurrentLoss = (double)(job?.loss ?? 0),
                        IsTraining = true,
                        Status = "Training"
                    };
                }
            }
            
            // Fallback to orchestrator status
            response = await _httpClient.GetAsync($"{OrchestratorUrl}/api/orchestrator/status");
            if (response.IsSuccessStatusCode)
            {
                var content = await response.Content.ReadAsStringAsync();
                var data = JsonConvert.DeserializeObject<dynamic>(content);
                
                return new TrainingProgress
                {
                    ModelName = data?.current_model?.ToString() ?? "Unknown",
                    IsTraining = data?.state?.ToString() == "training",
                    Status = data?.state?.ToString() ?? "idle"
                };
            }
        }
        catch { }
        
        return null;
    }
    
    public async Task StartFilteringAsync()
    {
        // Start orchestrator cycle
        await _httpClient.PostAsync($"{OrchestratorUrl}/api/orchestrator/start", null);
    }
    
    public async Task PauseFilteringAsync()
    {
        // Pause/stop orchestrator
        await _httpClient.PostAsync($"{OrchestratorUrl}/api/orchestrator/stop", null);
    }
    
    public async Task StopFilteringAsync()
    {
        await _httpClient.PostAsync($"{OrchestratorUrl}/api/orchestrator/stop", null);
    }
    
    // New methods for MediaForge services
    public async Task<bool> StartOrchestratorCycleAsync()
    {
        try
        {
            var response = await _httpClient.PostAsync($"{OrchestratorUrl}/api/orchestrator/cycle", null);
            return response.IsSuccessStatusCode;
        }
        catch { return false; }
    }
    
    public async Task<dynamic?> BuildDatasetAsync(string tier, string? name = null, bool regenerateCaptions = false)
    {
        try
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(new { tier, name, regenerate_captions = regenerateCaptions }),
                System.Text.Encoding.UTF8,
                "application/json"
            );
            var response = await _httpClient.PostAsync($"{DatasetBuilderUrl}/api/dataset/build", content);
            if (response.IsSuccessStatusCode)
            {
                return JsonConvert.DeserializeObject<dynamic>(await response.Content.ReadAsStringAsync());
            }
        }
        catch { }
        return null;
    }
    
    public async Task<dynamic?> GetRatingStatsAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{RatingStudioUrl}/api/stats");
            if (response.IsSuccessStatusCode)
            {
                return JsonConvert.DeserializeObject<dynamic>(await response.Content.ReadAsStringAsync());
            }
        }
        catch { }
        return null;
    }
    
    // AI Chat Integration
    public async Task<ChatResponse?> SendChatMessageAsync(string message)
    {
        try
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(new { message }),
                System.Text.Encoding.UTF8,
                "application/json"
            );
            var response = await _httpClient.PostAsync($"{LearningBrainUrl}/api/chat", content);
            if (response.IsSuccessStatusCode)
            {
                var data = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<ChatResponse>(data);
            }
        }
        catch { }
        return null;
    }
    
    // Generate AI Prompt based on preferences
    public async Task<PromptResponse?> GenerateSmartPromptAsync(string style = "tribal")
    {
        try
        {
            var response = await _httpClient.GetAsync($"{LearningBrainUrl}/api/suggest?style={style}");
            if (response.IsSuccessStatusCode)
            {
                var data = await response.Content.ReadAsStringAsync();
                var result = JsonConvert.DeserializeObject<dynamic>(data);
                if (result?.suggestions != null && result.suggestions.Count > 0)
                {
                    var first = result.suggestions[0];
                    return new PromptResponse
                    {
                        Success = true,
                        Positive = first.positive?.ToString(),
                        Negative = first.negative?.ToString(),
                        TagsUsed = ((IEnumerable<dynamic>)first.tags_used)?.Select(t => t.ToString()).ToList()
                    };
                }
            }
        }
        catch { }
        return null;
    }
    
    // Start LoRA Training
    public async Task<TrainingJobResponse?> StartTrainingAsync(string datasetPath, string baseModel, string tier = "bronze")
    {
        try
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(new { 
                    dataset_path = datasetPath, 
                    base_model = baseModel,
                    tier 
                }),
                System.Text.Encoding.UTF8,
                "application/json"
            );
            var response = await _httpClient.PostAsync($"{LoraTrainingUrl}/api/create", content);
            if (response.IsSuccessStatusCode)
            {
                var data = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<TrainingJobResponse>(data);
            }
        }
        catch { }
        return null;
    }
    
    // Get Learning Stats
    public async Task<LearningStats?> GetLearningStatsAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync($"{LearningBrainUrl}/api/stats");
            if (response.IsSuccessStatusCode)
            {
                var data = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<LearningStats>(data);
            }
        }
        catch { }
        return null;
    }
}

// Response models for new API calls
public class ChatResponse
{
    public bool Success { get; set; }
    public ChatLearned? Learned { get; set; }
    public List<string>? Actions { get; set; }
}

public class ChatLearned
{
    public List<string> Likes { get; set; } = new();
    public List<string> Dislikes { get; set; } = new();
}

public class PromptResponse
{
    public bool Success { get; set; }
    public string? Positive { get; set; }
    public string? Negative { get; set; }
    public List<string>? TagsUsed { get; set; }
}

public class TrainingJobResponse
{
    public bool Success { get; set; }
    public int JobId { get; set; }
    public string? ConfigPath { get; set; }
    public int ImageCount { get; set; }
}

public class LearningStats
{
    public int TotalImages { get; set; }
    public int RatedImages { get; set; }
    public int LearnedTags { get; set; }
    public int LearnedPreferences { get; set; }
    public int LearningEvents { get; set; }
    public int ChatInteractions { get; set; }
}
