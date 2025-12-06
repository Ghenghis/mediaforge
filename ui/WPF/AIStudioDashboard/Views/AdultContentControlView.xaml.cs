using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;

namespace AIStudioDashboard.Views
{
    public partial class AdultContentControlView : Window
    {
        private readonly HttpClient _client;
        private readonly DispatcherTimer _statusTimer;
        private const string API_BASE = "http://localhost:8205";

        public AdultContentControlView()
        {
            InitializeComponent();
            
            _client = new HttpClient();
            _client.Timeout = TimeSpan.FromSeconds(30);
            
            // Status update timer
            _statusTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromSeconds(2)
            };
            _statusTimer.Tick += async (s, e) => await UpdateStatus();
            _statusTimer.Start();
            
            // Initial load
            _ = LoadState();
        }

        private async Task LoadState()
        {
            try
            {
                var response = await _client.GetAsync($"{API_BASE}/api/wpf/state");
                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    var state = JsonSerializer.Deserialize<WpfState>(json);
                    
                    // Update UI
                    AgeSlider.Value = state?.age_slider_value ?? 18;
                    UpdateAgeDisplay((int)AgeSlider.Value);
                    
                    // Set automation mode
                    switch (state?.automation_mode)
                    {
                        case "manual": ManualMode.IsChecked = true; break;
                        case "semi_auto": SemiAutoMode.IsChecked = true; break;
                        case "full_auto": FullAutoMode.IsChecked = true; break;
                    }
                }
            }
            catch (Exception ex)
            {
                ShowError($"Failed to load state: {ex.Message}");
            }
        }

        private void AgeSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            int age = (int)e.NewValue;
            UpdateAgeDisplay(age);
            _ = SendAgeUpdate(age);
        }

        private void UpdateAgeDisplay(int age)
        {
            if (AgeDisplay == null) return;
            
            AgeDisplay.Text = age.ToString();
            
            string rating;
            string description;
            SolidColorBrush color;
            
            if (age >= 21)
            {
                rating = "X (21+)";
                description = "Full adult content enabled - 250+ images";
                color = new SolidColorBrush(Color.FromRgb(255, 64, 129));
                HighlightBadge(XBadge);
            }
            else if (age >= 18)
            {
                rating = "NC-17";
                description = "Adult explicit content allowed";
                color = new SolidColorBrush(Color.FromRgb(255, 153, 102));
                HighlightBadge(NC17Badge);
            }
            else if (age >= 17)
            {
                rating = "R";
                description = "Mature content allowed";
                color = new SolidColorBrush(Color.FromRgb(255, 204, 0));
                HighlightBadge(RBadge);
            }
            else if (age >= 13)
            {
                rating = "PG-13";
                description = "Teen content allowed";
                color = new SolidColorBrush(Color.FromRgb(0, 212, 255));
                HighlightBadge(PG13Badge);
            }
            else
            {
                rating = "PG";
                description = "General audiences only";
                color = new SolidColorBrush(Color.FromRgb(0, 255, 136));
                HighlightBadge(PGBadge);
            }
            
            RatingDisplay.Text = rating;
            RatingDisplay.Foreground = color;
            RatingDescription.Text = description;
        }

        private void HighlightBadge(Border activeBadge)
        {
            // Reset all badges
            var badges = new[] { PGBadge, PG13Badge, RBadge, NC17Badge, XBadge };
            foreach (var badge in badges)
            {
                if (badge != null)
                    badge.BorderThickness = new Thickness(0);
            }
            
            // Highlight active
            if (activeBadge != null)
            {
                activeBadge.BorderBrush = new SolidColorBrush(Colors.White);
                activeBadge.BorderThickness = new Thickness(2);
            }
        }

        private async Task SendAgeUpdate(int age)
        {
            try
            {
                var content = new StringContent(
                    JsonSerializer.Serialize(new { age }),
                    Encoding.UTF8,
                    "application/json");
                
                await _client.PostAsync($"{API_BASE}/api/wpf/age-slider", content);
            }
            catch { /* Ignore errors during slider movement */ }
        }

        private async void AutomationMode_Changed(object sender, RoutedEventArgs e)
        {
            string mode = "semi_auto";
            string description = "";
            
            if (ManualMode.IsChecked == true)
            {
                mode = "manual";
                description = "User controls all actions. AI provides suggestions only.";
            }
            else if (SemiAutoMode.IsChecked == true)
            {
                mode = "semi_auto";
                description = "AI assists when user gets stuck. Asks for confirmation on major actions.";
            }
            else if (FullAutoMode.IsChecked == true)
            {
                mode = "full_auto";
                description = "AI handles everything automatically. User can pause/resume anytime.";
            }
            
            AutomationDescription.Text = description;
            
            try
            {
                var content = new StringContent(
                    JsonSerializer.Serialize(new { mode }),
                    Encoding.UTF8,
                    "application/json");
                
                await _client.PostAsync($"{API_BASE}/api/wpf/automation-mode", content);
            }
            catch (Exception ex)
            {
                ShowError($"Failed to update mode: {ex.Message}");
            }
        }

        private async void StartPipeline_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                int totalImages = int.TryParse(TotalImagesInput.Text, out var t) ? t : 300;
                double adultRatio = double.TryParse(AdultRatioInput.Text, out var r) ? r / 100.0 : 0.83;
                string dwelling = (DwellingSelect.SelectedItem as ComboBoxItem)?.Content?.ToString()?.ToLower() ?? "teepee";
                
                var config = new
                {
                    total_images = totalImages,
                    adult_ratio = adultRatio,
                    dwelling,
                    adult_content = AgeSlider.Value >= 21
                };
                
                var content = new StringContent(
                    JsonSerializer.Serialize(config),
                    Encoding.UTF8,
                    "application/json");
                
                var response = await _client.PostAsync($"{API_BASE}/api/pipeline/start", content);
                var json = await response.Content.ReadAsStringAsync();
                
                if (response.IsSuccessStatusCode)
                {
                    PipelineStatus.Text = "RUNNING";
                    PipelineStatus.Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 136));
                }
                else
                {
                    ShowError($"Start failed: {json}");
                }
            }
            catch (Exception ex)
            {
                ShowError($"Start error: {ex.Message}");
            }
        }

        private async void PausePipeline_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                await _client.PostAsync($"{API_BASE}/api/pipeline/pause", null);
                PipelineStatus.Text = "PAUSED";
                PipelineStatus.Foreground = new SolidColorBrush(Color.FromRgb(255, 204, 0));
            }
            catch (Exception ex)
            {
                ShowError($"Pause error: {ex.Message}");
            }
        }

        private async void StopPipeline_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                await _client.PostAsync($"{API_BASE}/api/pipeline/stop", null);
                PipelineStatus.Text = "STOPPED";
                PipelineStatus.Foreground = new SolidColorBrush(Color.FromRgb(255, 107, 107));
            }
            catch (Exception ex)
            {
                ShowError($"Stop error: {ex.Message}");
            }
        }

        private async Task UpdateStatus()
        {
            try
            {
                var response = await _client.GetAsync($"{API_BASE}/api/pipeline/status");
                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    var status = JsonSerializer.Deserialize<PipelineStatusResponse>(json);
                    
                    // Update UI
                    PipelineStatus.Text = status?.pipeline_status?.ToUpper() ?? "IDLE";
                    ProgressDisplay.Text = $"{status?.progress:F1}%";
                    PipelineProgress.Value = status?.progress ?? 0;
                    GeneratedCount.Text = status?.generated.ToString() ?? "0";
                    FailedCount.Text = status?.failed.ToString() ?? "0";
                    AIFixesCount.Text = status?.ai_interventions.ToString() ?? "0";
                    
                    // Update status color
                    PipelineStatus.Foreground = status?.pipeline_status switch
                    {
                        "running" => new SolidColorBrush(Color.FromRgb(0, 255, 136)),
                        "paused" => new SolidColorBrush(Color.FromRgb(255, 204, 0)),
                        "completed" => new SolidColorBrush(Color.FromRgb(0, 212, 255)),
                        "failed" => new SolidColorBrush(Color.FromRgb(255, 107, 107)),
                        _ => new SolidColorBrush(Color.FromRgb(136, 136, 136))
                    };
                }
            }
            catch { /* Ignore status update errors */ }
        }

        private void ShowError(string message)
        {
            MessageBox.Show(message, "Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }

        protected override void OnClosed(EventArgs e)
        {
            _statusTimer?.Stop();
            _client?.Dispose();
            base.OnClosed(e);
        }
    }

    // Response classes
    public class WpfState
    {
        public int age_slider_value { get; set; }
        public string automation_mode { get; set; }
        public string current_view { get; set; }
    }

    public class PipelineStatusResponse
    {
        public string pipeline_status { get; set; }
        public string automation_mode { get; set; }
        public double progress { get; set; }
        public int total_images { get; set; }
        public int generated { get; set; }
        public int failed { get; set; }
        public int ai_interventions { get; set; }
    }
}
