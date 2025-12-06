using System;
using System.Net.Http;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace AIStudioDashboard.Views
{
    public partial class GenerationPipelineView : Window
    {
        private readonly HttpClient _httpClient;
        private string _currentRating = "PG";
        private string _currentCountry = "US";
        
        private const string COMFYUI_API = "http://127.0.0.1:8213";      // ComfyUI Automation API
        private const string PLAYWRIGHT_API = "http://127.0.0.1:8203";   // Playwright Automation
        private const string GUARDRAILS_API = "http://127.0.0.1:8200";   // Unified Gateway
        private const string ORCHESTRATOR_API = "http://127.0.0.1:8210"; // Master Orchestrator
        private const string QUALITY_GATE_API = "http://127.0.0.1:8216"; // Quality Gate

        public GenerationPipelineView()
        {
            InitializeComponent();
            _httpClient = new HttpClient();
            CheckConnections();
            LoadModelsAndStyles();
        }

        private async void LoadModelsAndStyles()
        {
            try
            {
                // Load available styles from ComfyUI API
                var stylesResponse = await _httpClient.GetStringAsync($"{COMFYUI_API}/api/comfyui/styles");
                var styles = JsonSerializer.Deserialize<JsonElement>(stylesResponse);
                
                // Load available presets
                var presetsResponse = await _httpClient.GetStringAsync($"{COMFYUI_API}/api/comfyui/presets");
                var presets = JsonSerializer.Deserialize<JsonElement>(presetsResponse);
                
                StatusText.Text = "Loaded styles and presets";
            }
            catch
            {
                StatusText.Text = "Using default styles";
            }
        }

        private async void CheckConnections()
        {
            // Check ComfyUI
            try
            {
                var response = await _httpClient.GetAsync($"{COMFYUI_API}/");
                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadAsStringAsync();
                    var data = JsonSerializer.Deserialize<JsonElement>(result);
                    var connected = data.GetProperty("connected").GetBoolean();
                    
                    ComfyUIIndicator.Fill = connected 
                        ? new SolidColorBrush(Color.FromRgb(76, 175, 80))
                        : new SolidColorBrush(Color.FromRgb(244, 67, 54));
                }
            }
            catch
            {
                ComfyUIIndicator.Fill = new SolidColorBrush(Color.FromRgb(244, 67, 54));
            }

            // Check Playwright
            try
            {
                var response = await _httpClient.GetAsync(PLAYWRIGHT_API);
                PlaywrightIndicator.Fill = response.IsSuccessStatusCode
                    ? new SolidColorBrush(Color.FromRgb(76, 175, 80))
                    : new SolidColorBrush(Color.FromRgb(244, 67, 54));
            }
            catch
            {
                PlaywrightIndicator.Fill = new SolidColorBrush(Color.FromRgb(244, 67, 54));
            }
        }

        private void Rating_Changed(object sender, SelectionChangedEventArgs e)
        {
            if (RatingSelector.SelectedItem is ComboBoxItem item && item.Tag is string rating)
            {
                _currentRating = rating;
                CurrentRatingDisplay.Text = $"Current: {rating} ({item.Content})";
            }
        }

        private async void Generate_Click(object sender, RoutedEventArgs e)
        {
            var prompt = PromptInput.Text;
            var negative = NegativeInput.Text;
            var model = (ModelSelector.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "SDXL Base 1.0";
            var workflow = (WorkflowSelector.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "txt2img_basic";
            var country = (CountrySelector.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "US";

            StatusText.Text = "Checking guardrails...";

            // First check guardrails
            try
            {
                var guardrailCheck = new
                {
                    prompt = prompt,
                    rating = _currentRating,
                    country = country
                };

                var checkContent = new StringContent(
                    JsonSerializer.Serialize(guardrailCheck),
                    System.Text.Encoding.UTF8,
                    "application/json");

                var guardrailResponse = await _httpClient.PostAsync($"{GUARDRAILS_API}/api/enforce", checkContent);
                var guardrailResult = await guardrailResponse.Content.ReadAsStringAsync();
                var guardrailData = JsonSerializer.Deserialize<JsonElement>(guardrailResult);

                var allowed = guardrailData.GetProperty("allowed").GetBoolean();
                
                if (!allowed)
                {
                    var message = guardrailData.GetProperty("message").GetString();
                    
                    // Check if auto-corrected
                    if (guardrailData.TryGetProperty("corrected_prompt", out var corrected) && 
                        corrected.GetString() != null)
                    {
                        var correctedPrompt = corrected.GetString();
                        var result = MessageBox.Show(
                            $"Prompt was auto-corrected for {_currentRating} rating.\n\n" +
                            $"Original: {prompt}\n\n" +
                            $"Corrected: {correctedPrompt}\n\n" +
                            "Use corrected prompt?",
                            "Guardrail Auto-Correction",
                            MessageBoxButton.YesNo,
                            MessageBoxImage.Warning);

                        if (result == MessageBoxResult.Yes)
                        {
                            prompt = correctedPrompt;
                            PromptInput.Text = correctedPrompt;
                        }
                        else
                        {
                            StatusText.Text = "Generation cancelled";
                            return;
                        }
                    }
                    else
                    {
                        MessageBox.Show(
                            $"Content blocked by guardrails.\n\n{message}",
                            "Guardrail Violation",
                            MessageBoxButton.OK,
                            MessageBoxImage.Error);
                        StatusText.Text = "Blocked by guardrails";
                        return;
                    }
                }
            }
            catch (Exception ex)
            {
                // Continue without guardrails if API unavailable
                System.Diagnostics.Debug.WriteLine($"Guardrails check failed: {ex.Message}");
            }

            StatusText.Text = "Sending to ComfyUI...";

            // Send to ComfyUI
            try
            {
                var generateRequest = new
                {
                    prompt = prompt,
                    negative_prompt = negative,
                    model = model,
                    workflow = workflow,
                    rating = _currentRating,
                    country = country
                };

                var content = new StringContent(
                    JsonSerializer.Serialize(generateRequest),
                    System.Text.Encoding.UTF8,
                    "application/json");

                var response = await _httpClient.PostAsync($"{COMFYUI_API}/api/generate", content);
                var result = await response.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<JsonElement>(result);

                if (data.TryGetProperty("success", out var success) && success.GetBoolean())
                {
                    var promptId = data.GetProperty("prompt_id").GetString();
                    StatusText.Text = $"Queued: {promptId}";
                    
                    RecentGenerations.Items.Insert(0, $"[{DateTime.Now:HH:mm:ss}] {_currentRating} - {prompt.Substring(0, Math.Min(30, prompt.Length))}...");
                    if (RecentGenerations.Items.Count > 10)
                        RecentGenerations.Items.RemoveAt(10);
                    
                    RefreshQueue_Click(null, null);
                }
                else if (data.TryGetProperty("error", out var error))
                {
                    MessageBox.Show($"Generation failed: {error.GetString()}", "Error");
                    StatusText.Text = "Generation failed";
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to connect to ComfyUI: {ex.Message}", "Connection Error");
                StatusText.Text = "ComfyUI not available";
            }
        }

        private async void RefreshQueue_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var response = await _httpClient.GetStringAsync($"{COMFYUI_API}/api/queue");
                var data = JsonSerializer.Deserialize<JsonElement>(response);

                if (data.TryGetProperty("queue_pending", out var pending))
                {
                    var pendingArray = pending.EnumerateArray();
                    int count = 0;
                    foreach (var _ in pendingArray) count++;
                    QueuePending.Text = count.ToString();
                }

                if (data.TryGetProperty("queue_running", out var running))
                {
                    var runningArray = running.EnumerateArray();
                    int count = 0;
                    foreach (var _ in runningArray) count++;
                    QueueRunning.Text = count.ToString();
                }
            }
            catch
            {
                QueuePending.Text = "?";
                QueueRunning.Text = "?";
            }
        }

        private async void ClearQueue_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                await _httpClient.PostAsync($"{COMFYUI_API}/api/queue/clear", null);
                QueuePending.Text = "0";
                QueueRunning.Text = "0";
                StatusText.Text = "Queue cleared";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to clear queue: {ex.Message}", "Error");
            }
        }

        private async void ConnectComfyUI_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Connecting to ComfyUI...";
            
            try
            {
                var response = await _httpClient.GetStringAsync($"{COMFYUI_API}/api/connection");
                var data = JsonSerializer.Deserialize<JsonElement>(response);
                var connected = data.GetProperty("connected").GetBoolean();

                if (connected)
                {
                    ComfyUIIndicator.Fill = new SolidColorBrush(Color.FromRgb(76, 175, 80));
                    StatusText.Text = "ComfyUI connected";
                    MessageBox.Show("ComfyUI is connected and ready!", "Connected", 
                        MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    ComfyUIIndicator.Fill = new SolidColorBrush(Color.FromRgb(244, 67, 54));
                    StatusText.Text = "ComfyUI not running";
                    MessageBox.Show(
                        "ComfyUI is not running.\n\n" +
                        "Please start ComfyUI first:\n" +
                        "1. Open ComfyUI folder\n" +
                        "2. Run run_nvidia_gpu.bat\n" +
                        "3. Wait for 'To see the GUI go to' message\n" +
                        "4. Click Connect again",
                        "ComfyUI Not Running",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                }
            }
            catch (Exception ex)
            {
                ComfyUIIndicator.Fill = new SolidColorBrush(Color.FromRgb(244, 67, 54));
                StatusText.Text = "Connection failed";
                MessageBox.Show(
                    $"Failed to connect: {ex.Message}\n\n" +
                    "Make sure the ComfyUI Integration API is running:\n" +
                    "python scripts/comfyui/comfyui_api.py",
                    "Connection Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }

        private async void StartPlaywright_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Starting Playwright browser...";

            try
            {
                var content = new StringContent(
                    JsonSerializer.Serialize(new { headless = false }),
                    System.Text.Encoding.UTF8,
                    "application/json");

                var response = await _httpClient.PostAsync($"{PLAYWRIGHT_API}/api/browser/start", content);
                var result = await response.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<JsonElement>(result);

                if (data.TryGetProperty("success", out var success) && success.GetBoolean())
                {
                    PlaywrightIndicator.Fill = new SolidColorBrush(Color.FromRgb(76, 175, 80));
                    StatusText.Text = "Playwright browser started";
                    MessageBox.Show("Playwright browser started successfully!", "Started",
                        MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else if (data.TryGetProperty("error", out var error))
                {
                    MessageBox.Show($"Failed to start browser: {error.GetString()}", "Error");
                    StatusText.Text = "Browser start failed";
                }
            }
            catch (Exception ex)
            {
                PlaywrightIndicator.Fill = new SolidColorBrush(Color.FromRgb(244, 67, 54));
                StatusText.Text = "Playwright not available";
                MessageBox.Show(
                    $"Failed to start Playwright: {ex.Message}\n\n" +
                    "Make sure Playwright is installed:\n" +
                    "pip install playwright\n" +
                    "playwright install chromium\n\n" +
                    "Then start the API:\n" +
                    "python scripts/automation/playwright_pipeline.py",
                    "Playwright Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }
    }
}
