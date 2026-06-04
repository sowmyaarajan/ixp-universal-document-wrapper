using System;
using System.Collections.Generic;
using System.Text.Json;
using IXPWrapper.Activities.Models;

namespace IXPWrapper.Activities.Services
{
    public static class ResponseParser
    {
        public static ExtractionResult Parse(JsonDocument resultDoc, string docId, int processingMs)
        {
            var result = new ExtractionResult
            {
                DocumentId       = docId,
                ProcessingTimeMs = processingMs,
                Status           = "Success",
            };

            try
            {
                var root       = resultDoc.RootElement;
                var extraction = root.GetProperty("result").GetProperty("extractionResult");
                var resultsDoc = extraction.GetProperty("ResultsDocument");

                result.DocumentType = resultsDoc
                    .GetProperty("DocumentTypeField")
                    .GetProperty("Value")
                    .GetString() ?? "Unknown";

                result.Pages = resultsDoc
                    .GetProperty("Bounds")
                    .GetProperty("PageCount")
                    .GetInt32();

                var fields      = resultsDoc.GetProperty("Fields");
                var confidences = new List<double>();

                foreach (var field in fields.EnumerateArray())
                {
                    foreach (var valueGroup in field.GetProperty("Values").EnumerateArray())
                    {
                        foreach (var component in valueGroup.GetProperty("Components").EnumerateArray())
                        {
                            if (component.GetProperty("FieldType").GetString() != "Internal")
                                continue;

                            var innerValues = component.GetProperty("Values");
                            if (innerValues.GetArrayLength() == 0) continue;

                            foreach (var sub in innerValues[0].GetProperty("Components").EnumerateArray())
                            {
                                var name   = sub.GetProperty("FieldName").GetString() ?? "";
                                var values = sub.GetProperty("Values");
                                if (values.GetArrayLength() == 0) continue;

                                var first = values[0];
                                var value = first.GetProperty("Value").GetString() ?? "";

                                JsonElement confEl;
                                var conf = first.TryGetProperty("Confidence", out confEl)
                                    ? confEl.GetDouble() : 0.0;

                                if (!string.IsNullOrEmpty(value) && value != name)
                                {
                                    result.Fields[name] = value;
                                    if (conf > 0) confidences.Add(conf);
                                }
                            }
                        }
                    }
                }

                result.Confidence = confidences.Count > 0
                    ? Math.Round(AverageOf(confidences), 4)
                    : 0.0;
            }
            catch (Exception ex)
            {
                result.Status       = "ParseError";
                result.ErrorMessage = "Failed to parse IXP response: " + ex.Message;
            }

            return result;
        }

        private static double AverageOf(List<double> values)
        {
            double sum = 0;
            foreach (var v in values) sum += v;
            return sum / values.Count;
        }
    }
}
