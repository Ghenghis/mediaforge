using System.Linq;

namespace AIStudioDashboard.Models;

public class ModelVersion
{
    public string Name { get; set; } = "";
    public string Version { get; set; } = "";
    public string Status { get; set; } = "Pending";  // Ready, Training, Pending, Failed
    public double AestheticScore { get; set; }
    public double AccuracyRate { get; set; }
    public double QualityScore { get; set; }
    public double FailureRate { get; set; }
    public string OverallGrade { get; set; } = "--";  // S+, S, A, B, C, D
    public double CompositeScore { get; set; }
    public DateTime? LastEvaluated { get; set; }
    public int TrainingSteps { get; set; }
    public int TotalSteps { get; set; }
    public double TrainingProgress => TotalSteps > 0 ? (double)TrainingSteps / TotalSteps * 100 : 0;
    
    // Training configuration
    public int LoraRank { get; set; }
    public double LearningRate { get; set; }
    public int DatasetSize { get; set; }
    public string BaseModel { get; set; } = "";
    
    public string StatusIcon => Status switch
    {
        "Ready" => "✓",
        "Training" => "⏳",
        "Pending" => "○",
        "Failed" => "✗",
        _ => "?"
    };
    
    public string GradeColor => OverallGrade switch
    {
        "S+" or "S" => "#FFD700",  // Gold
        "A+" or "A" or "A-" => "#22C55E",  // Green
        "B+" or "B" or "B-" => "#3B82F6",  // Blue
        "C+" or "C" or "C-" => "#F59E0B",  // Amber
        _ => "#64748B"  // Gray
    };
    
    public static ModelVersion CreateBronze() => new()
    {
        Name = "BRONZE",
        Version = "v1.0",
        Status = "Pending",
        LoraRank = 32,
        LearningRate = 1e-4,
        TotalSteps = 2000,
        BaseModel = "SDXL 1.0"
    };
    
    public static ModelVersion CreateSilver() => new()
    {
        Name = "SILVER",
        Version = "v2.0",
        Status = "Pending",
        LoraRank = 64,
        LearningRate = 5e-5,
        TotalSteps = 1000,
        BaseModel = "Bronze v1.0"
    };
    
    public static ModelVersion CreateGold() => new()
    {
        Name = "GOLD",
        Version = "v3.0",
        Status = "Pending",
        LoraRank = 64,
        LearningRate = 2e-5,
        TotalSteps = 500,
        BaseModel = "Silver v2.0"
    };
    
    public static ModelVersion CreatePlatinum() => new()
    {
        Name = "PLATINUM",
        Version = "v4.0",
        Status = "Pending",
        LoraRank = 128,
        LearningRate = 1e-5,
        TotalSteps = 1500,
        BaseModel = "Gold v3.0"
    };
}

public class TrainingProgress
{
    public string ModelName { get; set; } = "";
    public int CurrentStep { get; set; }
    public int TotalSteps { get; set; }
    public double CurrentLoss { get; set; }
    public double LearningRate { get; set; }
    public TimeSpan ElapsedTime { get; set; }
    public TimeSpan EstimatedRemaining { get; set; }
    public List<LossPoint> LossHistory { get; set; } = new();
    public double ProgressPercent => TotalSteps > 0 ? (double)CurrentStep / TotalSteps * 100 : 0;
    
    // Status properties
    public bool IsTraining { get; set; }
    public string Status { get; set; } = "idle";
}

public class LossPoint
{
    public int Step { get; set; }
    public double Loss { get; set; }
    public DateTime Timestamp { get; set; }
}

public class SystemHealth
{
    // External Services
    public bool LMStudioOnline { get; set; }
    public bool OllamaOnline { get; set; }
    public bool ComfyUIOnline { get; set; }
    
    // MediaForge Services
    public bool RatingStudioOnline { get; set; }
    public bool OrchestratorOnline { get; set; }
    public bool DatasetBuilderOnline { get; set; }
    public bool LoraTrainingOnline { get; set; }
    public bool LearningBrainOnline { get; set; }
    public string OrchestratorState { get; set; } = "unknown";
    
    // System Stats
    public double GpuUsage { get; set; }
    public double MemoryUsageGB { get; set; }
    public double MemoryTotalGB { get; set; }
    public string CurrentModel { get; set; } = "";
    public double ProcessingSpeedSeconds { get; set; }
    public DateTime LastUpdate { get; set; } = DateTime.Now;
    
    public double MemoryUsagePercent => MemoryTotalGB > 0 ? MemoryUsageGB / MemoryTotalGB * 100 : 0;
    
    // Service count summary
    public int OnlineServiceCount => new[] { 
        LMStudioOnline, OllamaOnline, ComfyUIOnline, 
        RatingStudioOnline, OrchestratorOnline, DatasetBuilderOnline,
        LoraTrainingOnline, LearningBrainOnline 
    }.Count(x => x);
    
    public int TotalServiceCount => 8;
}
