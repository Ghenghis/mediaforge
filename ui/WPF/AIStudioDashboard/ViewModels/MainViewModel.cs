using System.Collections.ObjectModel;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using AIStudioDashboard.Models;
using AIStudioDashboard.Services;

namespace AIStudioDashboard.ViewModels;

public partial class MainViewModel : ObservableObject
{
    private readonly IApiService _apiService;
    private readonly System.Timers.Timer _refreshTimer;
    
    [ObservableProperty]
    private SystemHealth _systemHealth = new();
    
    [ObservableProperty]
    private VideoStats _videoStats = new();
    
    [ObservableProperty]
    private CurrentTask _currentTask = new();
    
    [ObservableProperty]
    private ObservableCollection<ModelVersion> _modelVersions = new();
    
    [ObservableProperty]
    private ObservableCollection<FrameAnalysis> _recentFrames = new();
    
    [ObservableProperty]
    private TrainingProgress? _trainingProgress;
    
    [ObservableProperty]
    private bool _isProcessing;
    
    [ObservableProperty]
    private string _statusMessage = "Ready";
    
    [ObservableProperty]
    private string _selectedView = "Dashboard";
    
    public MainViewModel()
    {
        _apiService = new ApiService();
        
        InitializeModelVersions();
        InitializeMockData();
        
        // Refresh timer (1 second)
        _refreshTimer = new System.Timers.Timer(1000);
        _refreshTimer.Elapsed += async (s, e) => await RefreshDataAsync();
        _refreshTimer.Start();
    }
    
    private void InitializeModelVersions()
    {
        ModelVersions = new ObservableCollection<ModelVersion>
        {
            ModelVersion.CreateBronze(),
            ModelVersion.CreateSilver(),
            ModelVersion.CreateGold(),
            ModelVersion.CreatePlatinum()
        };
    }
    
    private void InitializeMockData()
    {
        // Mock system health
        SystemHealth = new SystemHealth
        {
            LMStudioOnline = true,
            OllamaOnline = true,
            GpuUsage = 78,
            MemoryUsageGB = 12.4,
            MemoryTotalGB = 16,
            CurrentModel = "qwen3-vl-8b-abliterated-caption-it",
            ProcessingSpeedSeconds = 4.07
        };
        
        // Mock video stats
        VideoStats = new VideoStats
        {
            TotalVideos = 423,
            ProcessedVideos = 156,
            ApprovedVideos = 42,
            RejectedVideos = 114,
            RejectionReasons = new Dictionary<string, int>
            {
                { "Male detected", 51 },
                { "Body type heavy", 32 },
                { "Low quality", 20 },
                { "Low attractiveness", 11 }
            }
        };
        
        // Mock current task
        CurrentTask = new CurrentTask
        {
            Stage = "FILTERING",
            VideoName = "xvideos_18yo_blonde_beauty...",
            CurrentFrame = 2,
            TotalFrames = 3,
            ProcessingTime = 3.2,
            LastAnalysis = new FrameAnalysis
            {
                Gender = "female",
                BodyType = "slim",
                Quality = 7,
                Attractiveness = 8,
                Approved = true
            }
        };
        
        // Mock recent frames
        RecentFrames = new ObservableCollection<FrameAnalysis>
        {
            new() { VideoName = "vid1.mp4", Quality = 7, Attractiveness = 8, Approved = true },
            new() { VideoName = "vid2.mp4", Quality = 8, Attractiveness = 7, Approved = true },
            new() { VideoName = "vid3.mp4", Quality = 3, Attractiveness = 4, Approved = false, RejectionReason = "Low quality" },
            new() { VideoName = "vid4.mp4", Quality = 6, Attractiveness = 6, Approved = true },
            new() { VideoName = "vid5.mp4", Quality = 7, Attractiveness = 7, Approved = true },
            new() { VideoName = "vid6.mp4", Quality = 2, Attractiveness = 3, Approved = false, RejectionReason = "Low quality" },
            new() { VideoName = "vid7.mp4", Quality = 9, Attractiveness = 9, Approved = true },
            new() { VideoName = "vid8.mp4", Quality = 8, Attractiveness = 8, Approved = true }
        };
    }
    
    private async Task RefreshDataAsync()
    {
        try
        {
            // Update from API when available
            var health = await _apiService.GetSystemHealthAsync();
            if (health != null)
            {
                await System.Windows.Application.Current.Dispatcher.InvokeAsync(() =>
                {
                    SystemHealth = health;
                });
            }
        }
        catch
        {
            // Silently handle refresh errors
        }
    }
    
    [RelayCommand]
    private async Task StartFilteringAsync()
    {
        IsProcessing = true;
        StatusMessage = "Starting video filtering...";
        
        try
        {
            await _apiService.StartFilteringAsync();
            StatusMessage = "Filtering in progress";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error: {ex.Message}";
        }
    }
    
    [RelayCommand]
    private async Task PauseFilteringAsync()
    {
        StatusMessage = "Pausing...";
        await _apiService.PauseFilteringAsync();
        IsProcessing = false;
        StatusMessage = "Paused";
    }
    
    [RelayCommand]
    private async Task StopFilteringAsync()
    {
        StatusMessage = "Stopping...";
        await _apiService.StopFilteringAsync();
        IsProcessing = false;
        StatusMessage = "Stopped";
    }
    
    [RelayCommand]
    private void OpenFolders()
    {
        var path = @"C:\Users\Admin\civitai\training";
        System.Diagnostics.Process.Start("explorer.exe", path);
    }
    
    [RelayCommand]
    private void OpenSettings()
    {
        SelectedView = "Settings";
    }
    
    [RelayCommand]
    private void NavigateTo(string view)
    {
        SelectedView = view;
    }
}
