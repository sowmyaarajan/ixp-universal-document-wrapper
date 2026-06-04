using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.IO;

namespace IXPWrapper.Activities.Services
{
    public class DUApiClient : IDisposable
    {
        private readonly HttpClient _http;
        private readonly string _host;
        private readonly string _clientId;
        private readonly string _clientSecret;
        private readonly string _orgUuid;
        private readonly string _tenantUuid;
        private readonly string _projectId;
        private readonly string _extractorId;
        private readonly int _timeoutMs;

        private const int PollIntervalMs = 5000;

        public DUApiClient(
            string host, string clientId, string clientSecret,
            string orgUuid, string tenantUuid, string projectId,
            string extractorId, int timeoutSeconds = 300)
        {
            _host         = host.TrimEnd('/');
            _clientId     = clientId;
            _clientSecret = clientSecret;
            _orgUuid      = orgUuid;
            _tenantUuid   = tenantUuid;
            _projectId    = projectId;
            _extractorId  = extractorId;
            _timeoutMs    = timeoutSeconds * 1000;
            _http         = new HttpClient { Timeout = TimeSpan.FromSeconds(60) };
        }

        private string ProjectBase =>
            string.Format("{0}/{1}/{2}/du_/api/framework/projects/{3}",
                _host, _orgUuid, _tenantUuid, _projectId);

        public async Task<string> GetTokenAsync()
        {
            var body = new FormUrlEncodedContent(new Dictionary<string, string>
            {
                { "grant_type",    "client_credentials" },
                { "client_id",     _clientId },
                { "client_secret", _clientSecret },
                { "scope",         "Du.Digitization.Api Du.Extraction.Api" },
            });

            var resp = await _http.PostAsync(_host + "/identity_/connect/token", body);
            resp.EnsureSuccessStatusCode();

            var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync());
            return doc.RootElement.GetProperty("access_token").GetString();
        }

        public async Task<string> DigitizerAsync(string pdfPath, string token)
        {
            using (var content = new MultipartFormDataContent())
            {
                var fileBytes   = File.ReadAllBytes(pdfPath);
                var fileContent = new ByteArrayContent(fileBytes);
                fileContent.Headers.ContentType = new MediaTypeHeaderValue("application/pdf");
                content.Add(fileContent, "file", Path.GetFileName(pdfPath));

                var req = new HttpRequestMessage(HttpMethod.Post,
                    ProjectBase + "/digitization/start?api-version=1")
                {
                    Content = content
                };
                req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

                var resp = await _http.SendAsync(req);
                resp.EnsureSuccessStatusCode();

                var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync());
                return doc.RootElement.GetProperty("documentId").GetString();
            }
        }

        public async Task PollDigitizationAsync(string docId, string token)
        {
            await PollAsync(ProjectBase + "/digitization/result/" + docId + "?api-version=1",
                token, "Digitization");
        }

        public async Task<string> StartExtractionAsync(string docId, string token)
        {
            var payload = JsonSerializer.Serialize(new { documentId = docId });
            var req = new HttpRequestMessage(HttpMethod.Post,
                ProjectBase + "/extractors/" + _extractorId + "/extraction/start?api-version=1")
            {
                Content = new StringContent(payload, Encoding.UTF8, "application/json")
            };
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

            var resp = await _http.SendAsync(req);
            resp.EnsureSuccessStatusCode();

            var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync());
            return doc.RootElement.GetProperty("resultUrl").GetString();
        }

        public async Task<JsonDocument> PollExtractionAsync(string resultUrl, string token)
        {
            return await PollAsync(resultUrl, token, "Extraction");
        }

        private async Task<JsonDocument> PollAsync(string url, string token, string label)
        {
            var deadline = DateTime.UtcNow.AddMilliseconds(_timeoutMs);

            while (DateTime.UtcNow < deadline)
            {
                await Task.Delay(PollIntervalMs);

                var req = new HttpRequestMessage(HttpMethod.Get, url);
                req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

                var resp = await _http.SendAsync(req);
                resp.EnsureSuccessStatusCode();

                var doc    = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync());
                var status = doc.RootElement.GetProperty("status").GetString();

                if (status == "Succeeded") return doc;

                if (status == "Failed")
                {
                    JsonElement errEl;
                    var errMsg = doc.RootElement.TryGetProperty("error", out errEl)
                        ? errEl.GetProperty("message").GetString()
                        : "Unknown error";
                    throw new InvalidOperationException(label + " failed: " + errMsg);
                }
            }

            throw new TimeoutException(
                label + " timed out after " + (_timeoutMs / 1000) + "s. " +
                "Image files may take longer — increase TimeoutSeconds property.");
        }

        public void Dispose() => _http.Dispose();
    }
}
