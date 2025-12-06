namespace AIStudioDashboard.Models;

public class VideoStats
{
    public int TotalVideos { get; set; }
    public int ProcessedVideos { get; set; }
    public int ApprovedVideos { get; set; }
    public int RejectedVideos { get; set; }
    public int PendingVideos => TotalVideos - ProcessedVideos;
    public double ApprovalRate => ProcessedVideos > 0 ? (double)ApprovedVideos / ProcessedVideos * 100 : 0;
    public double RejectionRate => ProcessedVideos > 0 ? (double)RejectedVideos / ProcessedVideos * 100 : 0;
    public double ProgressPercent => TotalVideos > 0 ? (double)ProcessedVideos / TotalVideos * 100 : 0;
    
    public Dictionary<string, int> RejectionReasons { get; set; } = new()
    {
        { "Male detected", 0 },
        { "Body type heavy", 0 },
        { "Low quality", 0 },
        { "Low attractiveness", 0 }
    };
}

public class FrameAnalysis
{
    public string VideoName { get; set; } = "";
    public int FrameNumber { get; set; }
    public string Gender { get; set; } = "";
    public string BodyType { get; set; } = "";
    public int Quality { get; set; }
    public int Attractiveness { get; set; }
    public int PeopleCount { get; set; }
    public bool Approved { get; set; }
    public string? RejectionReason { get; set; }
    public double AnalysisTimeSeconds { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.Now;
}

public class CurrentTask
{
    public string Stage { get; set; } = "IDLE";
    public string VideoName { get; set; } = "";
    public int CurrentFrame { get; set; }
    public int TotalFrames { get; set; }
    public double ProcessingTime { get; set; }
    public FrameAnalysis? LastAnalysis { get; set; }
}
