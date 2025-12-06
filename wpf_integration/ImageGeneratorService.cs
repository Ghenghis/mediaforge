using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace CivitaiImageGenerator.Services
{
    /// <summary>
    /// Service class for WPF integration with AI Learning Image Generation System
    /// Connects to the Python API server at http://127.0.0.1:8190
    /// </summary>
    public class ImageGeneratorService : IDisposable
    {
        private readonly HttpClient _client;
        private const string API_BASE = "http://127.0.0.1:8190";
        
        public ImageGeneratorService()
        {
            _client = new HttpClient();
            _client.Timeout = TimeSpan.FromMinutes(5);
        }
        
        #region GET Endpoints
        
        /// <summary>
        /// Get system status including ComfyUI connection and learning stats
        /// </summary>
        public async Task<SystemStatus> GetStatusAsync()
        {
            var response = await _client.GetStringAsync($"{API_BASE}/api/status");
            return JsonSerializer.Deserialize<SystemStatus>(response);
        }
        
        /// <summary>
        /// Get detailed learning statistics
        /// </summary>
        public async Task<LearningStats> GetStatsAsync()
        {
            var response = await _client.GetStringAsync($"{API_BASE}/api/stats");
            return JsonSerializer.Deserialize<LearningStats>(response);
        }
        
        /// <summary>
        /// Get all tag configuration for dropdowns
        /// </summary>
        public async Task<Dictionary<string, object>> GetConfigAsync()
        {
            var response = await _client.GetStringAsync($"{API_BASE}/api/config");
            return JsonSerializer.Deserialize<Dictionary<string, object>>(response);
        }
        
        /// <summary>
        /// Get current AI preference model
        /// </summary>
        public async Task<PreferenceModel> GetPreferenceModelAsync()
        {
            var response = await _client.GetStringAsync($"{API_BASE}/api/model");
            return JsonSerializer.Deserialize<PreferenceModel>(response);
        }
        
        /// <summary>
        /// Get list of generated images
        /// </summary>
        public async Task<List<GeneratedImage>> GetImagesAsync()
        {
            var response = await _client.GetStringAsync($"{API_BASE}/api/images");
            return JsonSerializer.Deserialize<List<GeneratedImage>>(response);
        }
        
        /// <summary>
        /// Get top preferred tags (user likes)
        /// </summary>
        public async Task<List<TagWeight>> GetPreferredTagsAsync()
        {
            var response = await _client.GetStringAsync($"{API_BASE}/api/preferred");
            return JsonSerializer.Deserialize<List<TagWeight>>(response);
        }
        
        /// <summary>
        /// Get avoided tags (user dislikes)
        /// </summary>
        public async Task<List<TagWeight>> GetAvoidedTagsAsync()
        {
            var response = await _client.GetStringAsync($"{API_BASE}/api/avoided");
            return JsonSerializer.Deserialize<List<TagWeight>>(response);
        }
        
        #endregion
        
        #region POST Endpoints
        
        /// <summary>
        /// Rate an image - AI will learn from this rating
        /// </summary>
        /// <param name="filename">Image filename</param>
        /// <param name="rating">Rating 1-5 (1-2 dislike, 3 neutral, 4-5 like)</param>
        public async Task<RatingResult> RateImageAsync(string filename, int rating)
        {
            var content = new StringContent(
                JsonSerializer.Serialize(new { filename, rating }),
                Encoding.UTF8, "application/json");
            
            var response = await _client.PostAsync($"{API_BASE}/api/rate", content);
            var json = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<RatingResult>(json);
        }
        
        /// <summary>
        /// Send chat message - AI will extract preferences and learn
        /// </summary>
        /// <param name="message">User message like "I like petite women with small breasts"</param>
        public async Task<ChatResult> SendChatAsync(string message)
        {
            var content = new StringContent(
                JsonSerializer.Serialize(new { message }),
                Encoding.UTF8, "application/json");
            
            var response = await _client.PostAsync($"{API_BASE}/api/chat", content);
            var json = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<ChatResult>(json);
        }
        
        /// <summary>
        /// Generate a single image using AI-learned preferences
        /// </summary>
        /// <param name="style">Style like "tribal"</param>
        /// <param name="prefix">Filename prefix</param>
        public async Task<GenerateResult> GenerateImageAsync(string style = "tribal", string prefix = "wpf_gen")
        {
            var content = new StringContent(
                JsonSerializer.Serialize(new { style, prefix }),
                Encoding.UTF8, "application/json");
            
            var response = await _client.PostAsync($"{API_BASE}/api/generate", content);
            var json = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<GenerateResult>(json);
        }
        
        /// <summary>
        /// Generate batch of images using AI-learned preferences
        /// </summary>
        /// <param name="count">Number of images</param>
        /// <param name="style">Style like "tribal"</param>
        /// <param name="prefix">Filename prefix</param>
        public async Task<BatchResult> GenerateBatchAsync(int count, string style = "tribal", string prefix = "batch")
        {
            var content = new StringContent(
                JsonSerializer.Serialize(new { count, style, prefix }),
                Encoding.UTF8, "application/json");
            
            var response = await _client.PostAsync($"{API_BASE}/api/generate-batch", content);
            var json = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<BatchResult>(json);
        }
        
        /// <summary>
        /// Get AI-optimized smart prompt based on learned preferences
        /// </summary>
        /// <param name="style">Style like "tribal"</param>
        public async Task<SmartPromptResult> GetSmartPromptAsync(string style = "tribal")
        {
            var content = new StringContent(
                JsonSerializer.Serialize(new { style }),
                Encoding.UTF8, "application/json");
            
            var response = await _client.PostAsync($"{API_BASE}/api/smart-prompt", content);
            var json = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<SmartPromptResult>(json);
        }
        
        /// <summary>
        /// Create training dataset from learned preferences
        /// </summary>
        /// <param name="name">Dataset name (optional)</param>
        public async Task<DatasetResult> CreateDatasetAsync(string name = null)
        {
            var content = new StringContent(
                JsonSerializer.Serialize(new { name }),
                Encoding.UTF8, "application/json");
            
            var response = await _client.PostAsync($"{API_BASE}/api/dataset", content);
            var json = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<DatasetResult>(json);
        }
        
        #endregion
        
        public void Dispose()
        {
            _client?.Dispose();
        }
    }
    
    #region Data Models
    
    public class SystemStatus
    {
        public string Api { get; set; }
        public string Comfyui { get; set; }
        public LearningStats Learning { get; set; }
        public string Timestamp { get; set; }
    }
    
    public class LearningStats
    {
        public int TotalImages { get; set; }
        public int RatedImages { get; set; }
        public int LearnedTags { get; set; }
        public int LearnedPreferences { get; set; }
        public int LearningEvents { get; set; }
        public int ChatInteractions { get; set; }
        public Dictionary<string, int> TagsByCategory { get; set; }
    }
    
    public class PreferenceModel
    {
        public string Version { get; set; }
        public Dictionary<string, TagPreference> TagPreferences { get; set; }
        public List<TagWeight> TopLiked { get; set; }
        public List<TagWeight> TopDisliked { get; set; }
    }
    
    public class TagPreference
    {
        public double Weight { get; set; }
        public string Category { get; set; }
        public int Likes { get; set; }
        public int Dislikes { get; set; }
    }
    
    public class TagWeight
    {
        public string Tag { get; set; }
        public double Weight { get; set; }
    }
    
    public class GeneratedImage
    {
        public string Filename { get; set; }
        public int SizeKb { get; set; }
        public double Time { get; set; }
    }
    
    public class RatingResult
    {
        public string Status { get; set; }
        public int Rating { get; set; }
        public int TagsUpdated { get; set; }
        public List<TagUpdate> Tags { get; set; }
    }
    
    public class TagUpdate
    {
        public string Tag { get; set; }
        public string Category { get; set; }
        public double Weight { get; set; }
    }
    
    public class ChatResult
    {
        public LearnedItems Learned { get; set; }
        public List<string> Actions { get; set; }
    }
    
    public class LearnedItems
    {
        public List<string> Likes { get; set; }
        public List<string> Dislikes { get; set; }
    }
    
    public class GenerateResult
    {
        public string Status { get; set; }
        public string Filename { get; set; }
        public long Seed { get; set; }
    }
    
    public class BatchResult
    {
        public string Status { get; set; }
        public int Count { get; set; }
    }
    
    public class SmartPromptResult
    {
        public string Positive { get; set; }
        public string Negative { get; set; }
        public List<string> Tags { get; set; }
    }
    
    public class DatasetResult
    {
        public string Status { get; set; }
        public string Path { get; set; }
        public DatasetStats Stats { get; set; }
    }
    
    public class DatasetStats
    {
        public int TotalPreferences { get; set; }
        public int TotalRatedImages { get; set; }
        public int LikedImages { get; set; }
        public int DislikedImages { get; set; }
    }
    
    #endregion
}
