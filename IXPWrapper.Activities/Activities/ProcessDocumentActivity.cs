using System;
using System.Activities;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Threading.Tasks;
using IXPWrapper.Activities.Models;
using IXPWrapper.Activities.Services;

namespace IXPWrapper.Activities.Activities
{
    [DisplayName("Process Document with IXP")]
    [Description("Converts any document to PDF, extracts fields using UiPath IXP (Gemini). Requires LibreOffice installed.")]
    public class ProcessDocumentActivity : AsyncCodeActivity
    {
        // ── Inputs ────────────────────────────────────────────────────────────

        [Category("File")]
        [DisplayName("File Path")]
        [Description("Full path to the input document (DOCX, XLSX, PPTX, CSV, PDF, PNG, JPG, etc.)")]
        [RequiredArgument]
        public InArgument<string> FilePath { get; set; }

        [Category("UiPath Credentials")]
        [DisplayName("UiPath Host")]
        [Description("e.g. https://cloud.uipath.com or https://staging.uipath.com")]
        [RequiredArgument]
        public InArgument<string> UiPathHost { get; set; }

        [Category("UiPath Credentials")]
        [DisplayName("Client ID")]
        [Description("External Application Client ID")]
        [RequiredArgument]
        public InArgument<string> ClientId { get; set; }

        [Category("UiPath Credentials")]
        [DisplayName("Client Secret")]
        [Description("External Application Client Secret")]
        [RequiredArgument]
        public InArgument<string> ClientSecret { get; set; }

        [Category("IXP Project")]
        [DisplayName("Org UUID")]
        [Description("Organisation UUID from DU API project discovery")]
        [RequiredArgument]
        public InArgument<string> OrgUUID { get; set; }

        [Category("IXP Project")]
        [DisplayName("Tenant UUID")]
        [Description("Tenant UUID from DU API project discovery")]
        [RequiredArgument]
        public InArgument<string> TenantUUID { get; set; }

        [Category("IXP Project")]
        [DisplayName("Project ID")]
        [Description("IXP project UUID")]
        [RequiredArgument]
        public InArgument<string> ProjectId { get; set; }

        [Category("IXP Project")]
        [DisplayName("Extractor ID")]
        [Description("e.g. gpt_ixp_5 — run setup.py to find this value")]
        [RequiredArgument]
        public InArgument<string> ExtractorId { get; set; }

        [Category("Options")]
        [DisplayName("Timeout (seconds)")]
        [Description("Max wait time. Images require longer (OCR). Default: 300.")]
        public InArgument<int> TimeoutSeconds { get; set; }

        // ── Outputs ───────────────────────────────────────────────────────────

        [Category("Output")]
        [DisplayName("Status")]
        [Description("Success / ValidationFailed / Failed")]
        public OutArgument<string> Status { get; set; }

        [Category("Output")]
        [DisplayName("Fields")]
        [Description("Extracted field name-value pairs")]
        public OutArgument<Dictionary<string, string>> Fields { get; set; }

        [Category("Output")]
        [DisplayName("Confidence")]
        [Description("Overall extraction confidence 0.0 - 1.0")]
        public OutArgument<double> Confidence { get; set; }

        [Category("Output")]
        [DisplayName("Document Type")]
        public OutArgument<string> DocumentType { get; set; }

        [Category("Output")]
        [DisplayName("Pages")]
        public OutArgument<int> Pages { get; set; }

        [Category("Output")]
        [DisplayName("Processing Time (ms)")]
        public OutArgument<int> ProcessingTimeMs { get; set; }

        // ── Execute ───────────────────────────────────────────────────────────

        protected override IAsyncResult BeginExecute(
            AsyncCodeActivityContext context, AsyncCallback callback, object state)
        {
            var filePath       = FilePath.Get(context);
            var host           = UiPathHost.Get(context);
            var clientId       = ClientId.Get(context);
            var clientSecret   = ClientSecret.Get(context);
            var orgUuid        = OrgUUID.Get(context);
            var tenantUuid     = TenantUUID.Get(context);
            var projectId      = ProjectId.Get(context);
            var extractorId    = ExtractorId.Get(context);
            var timeout        = TimeoutSeconds.Get(context);
            if (timeout <= 0) timeout = 300;

            var task = ProcessAsync(filePath, host, clientId, clientSecret,
                orgUuid, tenantUuid, projectId, extractorId, timeout);

            var tcs = new TaskCompletionSource<ExtractionResult>(state);
            task.ContinueWith(t =>
            {
                if (t.IsFaulted)
                    tcs.TrySetException(t.Exception.InnerExceptions);
                else if (t.IsCanceled)
                    tcs.TrySetCanceled();
                else
                    tcs.TrySetResult(t.Result);

                callback?.Invoke(tcs.Task);
            });

            return tcs.Task;
        }

        protected override void EndExecute(AsyncCodeActivityContext context, IAsyncResult result)
        {
            var task = (Task<ExtractionResult>)result;
            var r    = task.GetAwaiter().GetResult();

            Status.Set(context,          r.Status);
            Fields.Set(context,          r.Fields);
            Confidence.Set(context,      r.Confidence);
            DocumentType.Set(context,    r.DocumentType);
            Pages.Set(context,           r.Pages);
            ProcessingTimeMs.Set(context, r.ProcessingTimeMs);
        }

        private static async Task<ExtractionResult> ProcessAsync(
            string filePath, string host, string clientId, string clientSecret,
            string orgUuid, string tenantUuid, string projectId, string extractorId,
            int timeoutSeconds)
        {
            var started = DateTime.UtcNow;
            var tempDir = Path.Combine(Path.GetTempPath(), "ixp_act_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tempDir);

            try
            {
                var pdfPath = LibreOfficeConverter.EnsurePdf(filePath, tempDir);

                using (var client = new DUApiClient(host, clientId, clientSecret,
                    orgUuid, tenantUuid, projectId, extractorId, timeoutSeconds))
                {
                    var token     = await client.GetTokenAsync();
                    var docId     = await client.DigitizerAsync(pdfPath, token);
                    await client.PollDigitizationAsync(docId, token);
                    var resultUrl = await client.StartExtractionAsync(docId, token);
                    var resultDoc = await client.PollExtractionAsync(resultUrl, token);

                    var elapsedMs = (int)(DateTime.UtcNow - started).TotalMilliseconds;
                    return ResponseParser.Parse(resultDoc, docId, elapsedMs);
                }
            }
            finally
            {
                try { Directory.Delete(tempDir, true); } catch { }
            }
        }
    }
}
