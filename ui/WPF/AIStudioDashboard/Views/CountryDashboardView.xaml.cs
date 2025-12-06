using System;
using System.Net.Http;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;

namespace AIStudioDashboard.Views
{
    public partial class CountryDashboardView : Window
    {
        private readonly HttpClient _httpClient;
        private string _currentCountry = "US";
        
        private const string COUNTRY_API = "http://127.0.0.1:8199";

        public CountryDashboardView()
        {
            InitializeComponent();
            _httpClient = new HttpClient();
            LoadCountryData("US");
        }

        private void CountrySelector_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (CountrySelector.SelectedItem is ComboBoxItem item && item.Tag is string code)
            {
                _currentCountry = code;
                LoadCountryData(code);
            }
        }

        private async void LoadCountryData(string countryCode)
        {
            try
            {
                var response = await _httpClient.GetStringAsync($"{COUNTRY_API}/api/country/{countryCode}");
                var country = JsonSerializer.Deserialize<JsonElement>(response);
                
                CountryName.Text = country.GetProperty("name").GetString() ?? countryCode;
                CountryCode.Text = countryCode;
                
                if (country.TryGetProperty("system", out var system))
                    RatingSystem.Text = system.GetString() ?? "Unknown";
                
                if (country.TryGetProperty("adult_legal_age", out var age))
                    AdultAge.Text = age.GetInt32().ToString();
                
                if (country.TryGetProperty("explicit_banned", out var banned))
                {
                    var isBanned = banned.GetBoolean();
                    ExplicitStatus.Text = isBanned ? "BANNED" : "Allowed";
                    ExplicitStatus.Foreground = isBanned 
                        ? new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(244, 67, 54))
                        : new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(76, 175, 80));
                }
                
                if (country.TryGetProperty("max_our_rating", out var maxRating))
                    MaxRating.Text = maxRating.GetString() ?? "Unknown";
            }
            catch (Exception ex)
            {
                // Use defaults if API unavailable
                System.Diagnostics.Debug.WriteLine($"Country API error: {ex.Message}");
                SetDefaultCountryData(countryCode);
            }
        }

        private void SetDefaultCountryData(string code)
        {
            var defaults = new System.Collections.Generic.Dictionary<string, (string name, string system, int age, bool banned, string max)>
            {
                { "US", ("United States", "MPAA", 18, false, "EXTREME") },
                { "GB", ("United Kingdom", "BBFC", 18, false, "EXTREME") },
                { "DE", ("Germany", "FSK", 18, false, "EXTREME") },
                { "FR", ("France", "CNC", 18, false, "EXTREME") },
                { "JP", ("Japan", "EIRIN", 18, false, "EXTREME") },
                { "AU", ("Australia", "ACB", 18, false, "X") },
                { "CA", ("Canada", "CHVRS", 18, false, "EXTREME") },
                { "NL", ("Netherlands", "Kijkwijzer", 16, false, "EXTREME") },
                { "SA", ("Saudi Arabia", "GCAM", 21, true, "NC-18") },
                { "CN", ("China", "SARFT", 18, true, "PG-13") }
            };

            if (defaults.TryGetValue(code, out var data))
            {
                CountryName.Text = data.name;
                CountryCode.Text = code;
                RatingSystem.Text = data.system;
                AdultAge.Text = data.age.ToString();
                ExplicitStatus.Text = data.banned ? "BANNED" : "Allowed";
                ExplicitStatus.Foreground = data.banned 
                    ? new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(244, 67, 54))
                    : new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(76, 175, 80));
                MaxRating.Text = data.max;
            }
        }

        private async void CheckCompliance_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var content = new StringContent(
                    JsonSerializer.Serialize(new { rating = "R", country = _currentCountry }),
                    System.Text.Encoding.UTF8,
                    "application/json");
                
                var response = await _httpClient.PostAsync($"{COUNTRY_API}/api/check-compliance", content);
                var result = await response.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<JsonElement>(result);
                
                var compliant = data.GetProperty("compliant").GetBoolean();
                var message = data.GetProperty("message").GetString();
                
                MessageBox.Show(
                    $"Country: {_currentCountry}\n" +
                    $"Compliant: {(compliant ? "YES" : "NO")}\n" +
                    $"Message: {message}",
                    "Compliance Check",
                    MessageBoxButton.OK,
                    compliant ? MessageBoxImage.Information : MessageBoxImage.Warning);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Country: {_currentCountry}\n" +
                    $"Status: Unable to verify (API offline)\n" +
                    $"Using default settings.",
                    "Compliance Check",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);
            }
        }
    }
}
