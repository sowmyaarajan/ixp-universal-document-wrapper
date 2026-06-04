using System.Collections.Generic;

namespace IXPWrapper.Activities.Models
{
    public class ExtractionResult
    {
        public string Status { get; set; } = "Unknown";
        public string DocumentId { get; set; } = string.Empty;
        public string DocumentType { get; set; } = string.Empty;
        public double Confidence { get; set; }
        public int Pages { get; set; }
        public Dictionary<string, string> Fields { get; set; } = new Dictionary<string, string>();
        public int ProcessingTimeMs { get; set; }
        public string ErrorMessage { get; set; }
    }
}
