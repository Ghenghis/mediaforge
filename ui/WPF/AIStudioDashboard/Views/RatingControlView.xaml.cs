using System;
using System.Net.Http;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;

namespace AIStudioDashboard.Views
{
    public partial class RatingControlView : Window
    {
        private readonly HttpClient _httpClient;
        private string _currentRating = "PG";
        private string _currentCategory = "family_safe";
        
        // API endpoints
        private const string RATING_UI_API = "http://127.0.0.1:8208";    // Rating UI API
        private const string GUARDRAILS_API = "http://127.0.0.1:8200";   // Unified Gateway
        private const string COUNTRY_API = "http://127.0.0.1:8199";      // Country Rating API
        private const string ORCHESTRATOR_API = "http://127.0.0.1:8210"; // Master Orchestrator

        public RatingControlView()
        {
            InitializeComponent();
            _httpClient = new HttpClient();
            LoadCurrentSettings();
        }

        private async void LoadCurrentSettings()
        {
            try
            {
                var response = await _httpClient.GetStringAsync($"{RATING_UI_API}/api/stats");
                var stats = JsonSerializer.Deserialize<JsonElement>(response);
                
                if (stats.TryGetProperty("total_images", out var total))
                {
                    // Update UI with stats if controls exist
                    System.Diagnostics.Debug.WriteLine($"Total images: {total.GetInt32()}");
                }
            }
            catch (Exception ex)
            {
                // API not available - use defaults
                System.Diagnostics.Debug.WriteLine($"Rating API not available: {ex.Message}");
            }
        }

        private void Category_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is string category)
            {
                _currentCategory = category;
                HighlightCategory(category);
                
                // Show appropriate ratings for category
                switch (category)
                {
                    case "family_safe":
                        UpdateRating("PG", "Family Safe - Parental Guidance", "#4CAF50");
                        break;
                    case "teen":
                        UpdateRating("NC-15", "Teen - 15+", "#2196F3");
                        break;
                    case "adult_entry":
                        UpdateRating("NC-18", "Adult Entry - 18+", "#FF9800");
                        break;
                    case "adult_soft":
                        UpdateRating("SOFT", "Adult Soft - 18+", "#9C27B0");
                        break;
                    case "adult_explicit":
                        UpdateRating("HARD", "Adult Explicit - 21+", "#F44336");
                        break;
                }
            }
        }

        private void UpdateRating(string rating, string description, string color)
        {
            _currentRating = rating;
            CurrentRatingText.Text = rating;
            CurrentRatingDesc.Text = description;
            
            var brush = new System.Windows.Media.BrushConverter().ConvertFromString(color) as System.Windows.Media.Brush;
            if (brush != null)
            {
                CurrentRatingText.Foreground = brush;
            }
        }

        private void HighlightCategory(string category)
        {
            // Visual feedback for selected category
        }

        private void SettingsGear_Click(object sender, RoutedEventArgs e)
        {
            // Show settings popup with About dropdown
            var settingsInfo = @"CONTENT PROTECTION SYSTEM

GLOBAL FORBIDDEN TERMS: 47
- Minor-related: 25 terms (child, minor, underage, loli, etc.)
- Illegal content: 15 terms (abuse, assault, rape, etc.)
- Extreme violence: 7 terms (snuff, torture porn, etc.)

RATINGS PROTECTED: 22 Levels
Family Safe (5): EL, L, G, PG, PG-13
Teen (4): NC-14, NC-15, NC-16, NC-17
Adult Entry (3): NC-18, NC-19, NC-20
Adult Soft (4): SOFT, SOFTCORE, MED, R
Adult Explicit (5): HARD, HC, X, XXX, EXTREME

GUARDRAIL LEVELS: 6
1 - Maximum Protection (Children)
2 - Family Protection
3 - Teen Protection
4 - Adult Entry (Verification)
5 - Adult Soft (Release)
6 - Adult Explicit (Full Release)

COUNTRIES: 197
- Explicit Banned: 45 countries
- Adult Age 21+: 11 countries
- Standard 18+: 181 countries";

            MessageBox.Show(settingsInfo, "About - Content Protection", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void ReleaseRestrictions_Click(object sender, RoutedEventArgs e)
        {
            var result = MessageBox.Show(
                "This will release adult content restrictions.\n\nYou must be of legal age in your country.\n\nContinue?",
                "Release Restrictions",
                MessageBoxButton.YesNo,
                MessageBoxImage.Warning);
            
            if (result == MessageBoxResult.Yes)
            {
                try
                {
                    // Call admin API to release restrictions
                    var content = new StringContent(
                        JsonSerializer.Serialize(new { action = "release" }),
                        System.Text.Encoding.UTF8,
                        "application/json");
                    
                    await _httpClient.PostAsync($"{GUARDRAILS_API}/api/release", content);
                    
                    MessageBox.Show("Restrictions released for this session.", "Success", 
                        MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Failed to release restrictions: {ex.Message}", "Error",
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void LockAll_Click(object sender, RoutedEventArgs e)
        {
            UpdateRating("PG", "Family Safe - Parental Guidance", "#4CAF50");
            _currentCategory = "family_safe";
            
            AutoTaggingToggle.IsChecked = true;
            GuardrailsToggle.IsChecked = true;
            CountryComplianceToggle.IsChecked = true;
            
            MessageBox.Show("All restrictions locked. Rating set to PG.", "Locked", 
                MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void Apply_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var settings = new
                {
                    rating = _currentRating,
                    category = _currentCategory,
                    auto_tagging = AutoTaggingToggle.IsChecked ?? false,
                    guardrails = GuardrailsToggle.IsChecked ?? true,
                    country_compliance = CountryComplianceToggle.IsChecked ?? true
                };
                
                var content = new StringContent(
                    JsonSerializer.Serialize(settings),
                    System.Text.Encoding.UTF8,
                    "application/json");
                
                await _httpClient.PostAsync($"{RATING_UI_API}/api/settings", content);
                
                MessageBox.Show($"Settings applied.\nRating: {_currentRating}", "Applied",
                    MessageBoxButton.OK, MessageBoxImage.Information);
                
                this.DialogResult = true;
                this.Close();
            }
            catch (Exception ex)
            {
                // Apply locally even if API fails
                MessageBox.Show($"Settings applied locally.\nRating: {_currentRating}", "Applied",
                    MessageBoxButton.OK, MessageBoxImage.Information);
                this.Close();
            }
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            this.DialogResult = false;
            this.Close();
        }
    }
}
