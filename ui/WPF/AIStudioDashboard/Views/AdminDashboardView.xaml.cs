using System;
using System.Net.Http;
using System.Text.Json;
using System.Windows;

namespace AIStudioDashboard.Views
{
    public partial class AdminDashboardView : Window
    {
        private readonly HttpClient _httpClient;
        private string _adminToken;
        
        private const string ADMIN_API = "http://127.0.0.1:8201";
        private const string GUARDRAILS_API = "http://127.0.0.1:8200";
        private const string SUPABASE_API = "http://127.0.0.1:8202";
        private const string ORCHESTRATOR_API = "http://127.0.0.1:8210";
        private const string TRAINING_API = "http://127.0.0.1:8214";
        private const string QUALITY_GATE_API = "http://127.0.0.1:8216";
        private const string WORKFLOW_API = "http://127.0.0.1:8221";

        public AdminDashboardView()
        {
            InitializeComponent();
            _httpClient = new HttpClient();
            Login();
        }

        private async void Login()
        {
            try
            {
                var content = new StringContent(
                    JsonSerializer.Serialize(new { username = "admin", password = "admin123" }),
                    System.Text.Encoding.UTF8,
                    "application/json");
                
                var response = await _httpClient.PostAsync($"{ADMIN_API}/api/login", content);
                var result = await response.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<JsonElement>(result);
                
                if (data.TryGetProperty("token", out var token))
                {
                    _adminToken = token.GetString();
                    _httpClient.DefaultRequestHeaders.Authorization = 
                        new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", _adminToken);
                    LoadStats();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Admin login error: {ex.Message}");
            }
        }

        private async void LoadStats()
        {
            try
            {
                // Admin stats
                var adminResponse = await _httpClient.GetStringAsync($"{ADMIN_API}/api/stats");
                var adminStats = JsonSerializer.Deserialize<JsonElement>(adminResponse);
                
                if (adminStats.TryGetProperty("total_users", out var users))
                    TotalUsers.Text = users.GetInt32().ToString();
                if (adminStats.TryGetProperty("active_sessions", out var sessions))
                    ActiveSessions.Text = sessions.GetInt32().ToString();
                if (adminStats.TryGetProperty("flagged_users", out var flagged))
                    FlaggedUsers.Text = flagged.GetInt32().ToString();
                
                // Guardrails stats
                var guardrailsResponse = await _httpClient.GetStringAsync($"{GUARDRAILS_API}/api/stats");
                var guardrailsStats = JsonSerializer.Deserialize<JsonElement>(guardrailsResponse);
                
                if (guardrailsStats.TryGetProperty("total_violations", out var violations))
                    TotalViolations.Text = violations.GetInt32().ToString();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Stats error: {ex.Message}");
            }
        }

        private void FullAccess_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "Full Access Mode ENABLED\n\n" +
                "All restrictions bypassed:\n" +
                "- Rating limits: DISABLED\n" +
                "- Country restrictions: DISABLED\n" +
                "- Guardrails: MONITORING ONLY\n\n" +
                "Use responsibly for testing only.",
                "Full Access Mode",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
        }

        private void BypassRatings_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "Rating Bypass ACTIVE\n\n" +
                "All 22 rating levels accessible.\n" +
                "No content restrictions applied.",
                "Rating Bypass",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void BypassCountry_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "Country Bypass ACTIVE\n\n" +
                "All 197 country restrictions bypassed.\n" +
                "Content available regardless of location.",
                "Country Bypass",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void TestViolation_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "Test Violation Mode\n\n" +
                "This allows testing content that would normally be blocked.\n" +
                "Violations are logged but not enforced.\n\n" +
                "Test prompt: 'explicit content test'\n" +
                "Result: WOULD BE BLOCKED (logged only)",
                "Test Violation",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void TestForbidden_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "Forbidden Terms Test\n\n" +
                "47 globally forbidden terms:\n\n" +
                "Minor-related (25): child, minor, underage, loli...\n" +
                "Illegal content (15): abuse, assault, rape...\n" +
                "Extreme violence (7): snuff, torture porn...\n\n" +
                "These are ALWAYS blocked, even for admin testing.\n" +
                "Admin can VIEW logs but not bypass global forbidden.",
                "Forbidden Terms",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
        }

        private async void ViewLogs_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var response = await _httpClient.GetStringAsync($"{ADMIN_API}/api/actions");
                var actions = JsonSerializer.Deserialize<JsonElement>(response);
                
                ActionsLog.Items.Clear();
                foreach (var action in actions.EnumerateArray())
                {
                    var timestamp = action.GetProperty("created_at").GetString();
                    var actionType = action.GetProperty("action").GetString();
                    var username = action.GetProperty("username").GetString();
                    ActionsLog.Items.Add($"[{timestamp}] {username}: {actionType}");
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to load logs: {ex.Message}", "Error");
            }
        }

        private void UserManagement_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "User Management\n\n" +
                "Features:\n" +
                "- View all users\n" +
                "- Flag suspicious users\n" +
                "- Review access patterns\n" +
                "- Ban/unban users\n" +
                "- Reset user sessions",
                "User Management",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void SystemConfig_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "System Configuration\n\n" +
                "API Ports:\n" +
                "- Rating System: 8198\n" +
                "- Country Ratings: 8199\n" +
                "- Guardrails: 8200\n" +
                "- Admin System: 8201\n" +
                "- Supabase Local: 8202\n" +
                "- Playwright: 8203\n" +
                "- ComfyUI: 8204\n\n" +
                "Data Paths:\n" +
                "- Ratings: data/comprehensive_ratings.json\n" +
                "- Countries: data/international_ratings.json\n" +
                "- Guardrails: data/guardrails_index.json",
                "System Config",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private async void RefreshStatus_Click(object sender, RoutedEventArgs e)
        {
            var endpoints = new (string url, string name, System.Windows.Controls.TextBlock status)[]
            {
                ("http://127.0.0.1:8200", "Guardrails", GuardrailsStatus),
                ("http://127.0.0.1:8201", "Admin", AdminStatus),
                ("http://127.0.0.1:8203", "Playwright", PlaywrightStatus),
                ("http://127.0.0.1:8210", "Orchestrator", null),
                ("http://127.0.0.1:8213", "ComfyUI Auto", ComfyUIStatus),
                ("http://127.0.0.1:8214", "Training", null),
                ("http://127.0.0.1:8216", "Quality Gate", null),
                ("http://127.0.0.1:8221", "Workflows", null)
            };

            int online = 0;
            int total = endpoints.Length;

            foreach (var (url, name, textBlock) in endpoints)
            {
                try
                {
                    var client = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
                    var response = await client.GetAsync(url);
                    bool isOnline = response.IsSuccessStatusCode;
                    if (isOnline) online++;
                    
                    if (textBlock != null)
                    {
                        textBlock.Text = isOnline ? "ONLINE" : "ERROR";
                        textBlock.Foreground = isOnline 
                            ? new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(76, 175, 80))
                            : new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(244, 67, 54));
                    }
                }
                catch
                {
                    if (textBlock != null)
                    {
                        textBlock.Text = "OFFLINE";
                        textBlock.Foreground = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(244, 67, 54));
                    }
                }
            }
            
            // Update overall status
            System.Diagnostics.Debug.WriteLine($"Services: {online}/{total} online");
        }

        private async void Logout_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                await _httpClient.PostAsync($"{ADMIN_API}/api/logout", null);
            }
            catch { }
            
            this.Close();
        }
    }
}
