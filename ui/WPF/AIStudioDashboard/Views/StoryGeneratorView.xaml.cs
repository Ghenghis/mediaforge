using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;

namespace AIStudioDashboard.Views
{
    public partial class StoryGeneratorView : Window
    {
        private readonly HttpClient _httpClient;
        private const string FRONTIER_API = "http://127.0.0.1:8195";     // Frontier Stories API
        private const string VOICE_API = "http://127.0.0.1:8212";        // Voice Integration API
        private const string ORCHESTRATOR_API = "http://127.0.0.1:8210"; // Master Orchestrator
        private string _selectedRating = "PG";
        private bool _apiConnected = false;
        
        public StoryGeneratorView()
        {
            InitializeComponent();
            _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
            
            // Setup rating toggle buttons
            SetupRatingButtons();
            
            // Load initial stats
            Loaded += async (s, e) => await LoadStats();
        }
        
        private void SetupRatingButtons()
        {
            // Family safe ratings
            var familyRatings = new[] { RatingEL, RatingL, RatingPG, RatingPG13, RatingPG17 };
            // Adult ratings
            var adultRatings = new[] { RatingSOFT, RatingMED, RatingR, RatingHARD, RatingHC, RatingX, RatingXXX };
            
            foreach (var btn in familyRatings)
            {
                btn.Checked += (s, e) => SelectRating(btn, familyRatings, adultRatings);
            }
            
            foreach (var btn in adultRatings)
            {
                btn.Checked += (s, e) => SelectRating(btn, familyRatings, adultRatings);
            }
        }
        
        private void SelectRating(ToggleButton selected, ToggleButton[] family, ToggleButton[] adult)
        {
            // Uncheck all others
            foreach (var btn in family) if (btn != selected) btn.IsChecked = false;
            foreach (var btn in adult) if (btn != selected) btn.IsChecked = false;
            
            // Get rating code from button name
            _selectedRating = selected.Name.Replace("Rating", "");
            StatusText.Text = $"Selected rating: {_selectedRating}";
        }
        
        private async Task LoadStats()
        {
            try
            {
                var response = await _httpClient.GetStringAsync($"{FRONTIER_API}/api/stats");
                var stats = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(response);
                
                if (stats != null)
                {
                    _apiConnected = true;
                    StatActors.Text = stats.TryGetValue("actors", out var a) ? a.GetInt32().ToString() : "0";
                    StatFamilies.Text = stats.TryGetValue("families", out var f) ? f.GetInt32().ToString() : "0";
                    StatImages.Text = stats.TryGetValue("images", out var i) ? i.GetInt32().ToString() : "0";
                    StatDialogs.Text = stats.TryGetValue("dialogs", out var d) ? d.GetInt32().ToString() : "0";
                    StatQueue.Text = stats.TryGetValue("pending_queue", out var q) ? q.GetInt32().ToString() : "0";
                }
                
                StatusText.Text = "Connected to Frontier Stories API";
            }
            catch (Exception ex)
            {
                _apiConnected = false;
                StatusText.Text = $"API offline - using local mode: {ex.Message}";
            }
        }
        
        private async Task<T?> PostAsync<T>(string endpoint, object data)
        {
            try
            {
                var json = JsonSerializer.Serialize(data);
                var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync($"{FRONTIER_API}{endpoint}", content);
                var responseJson = await response.Content.ReadAsStringAsync();
                return JsonSerializer.Deserialize<T>(responseJson);
            }
            catch
            {
                return default;
            }
        }
        
        private async void GenerateActors_Click(object sender, RoutedEventArgs e)
        {
            if (!int.TryParse(ActorCount.Text, out int count)) count = 525;
            
            StatusText.Text = $"Generating {count} actors...";
            
            var result = await PostAsync<Dictionary<string, int>>("/api/actors/generate", new { count });
            
            if (result != null)
            {
                StatusText.Text = $"Created {result.GetValueOrDefault("actors", 0)} actors in {result.GetValueOrDefault("families", 0)} families!";
                await LoadStats();
            }
            else
            {
                StatusText.Text = "Error generating actors";
            }
        }
        
        private async void ViewActors_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                StatusText.Text = "Loading actors...";
                var response = await _httpClient.GetStringAsync($"{FRONTIER_API}/api/actors?limit=100");
                var actors = JsonSerializer.Deserialize<List<Dictionary<string, object>>>(response);
                
                if (actors != null)
                {
                    ActorList.ItemsSource = actors;
                    StatusText.Text = $"Loaded {actors.Count} actors";
                }
            }
            catch (Exception ex)
            {
                StatusText.Text = $"Error: {ex.Message}";
            }
        }
        
        private async void ViewFamilies_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                StatusText.Text = "Loading families...";
                var response = await _httpClient.GetStringAsync($"{FRONTIER_API}/api/families");
                var families = JsonSerializer.Deserialize<List<Dictionary<string, object>>>(response);
                
                StatusText.Text = $"Loaded {families?.Count ?? 0} families";
            }
            catch (Exception ex)
            {
                StatusText.Text = $"Error: {ex.Message}";
            }
        }
        
        private async void GenerateAll_Click(object sender, RoutedEventArgs e)
        {
            if (!int.TryParse(BatchSize.Text, out int batchSize)) batchSize = 50;
            
            StatusText.Text = $"Generating images for {batchSize} actors ({_selectedRating})...";
            
            var result = await PostAsync<Dictionary<string, int>>("/api/images/generate-all", 
                new { batch_size = batchSize, content_rating = _selectedRating });
            
            if (result != null)
            {
                StatusText.Text = $"Queued {result.GetValueOrDefault("queued", 0)} images!";
                await LoadStats();
            }
            else
            {
                StatusText.Text = "Error generating images";
            }
        }
        
        private void GenerateFamily_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Select a family from the list first";
        }
        
        private void ViewQueue_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Queue viewer coming soon";
        }
    }
}
