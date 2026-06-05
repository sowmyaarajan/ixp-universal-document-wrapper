using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;

namespace IXPWrapper.Activities.Services
{
    public static class LibreOfficeConverter
    {
        private static readonly string[] WindowsPaths =
        {
            @"C:\Program Files\LibreOffice\program\soffice.exe",
            @"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        };

        private static readonly string[] LinuxBinaries = { "soffice", "libreoffice" };

        private static readonly HashSet<string> SupportedExtensions =
            new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".csv",
                ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp",
            };

        public static string EnsurePdf(string inputPath, string tempDir)
        {
            var ext = Path.GetExtension(inputPath);

            if (string.Equals(ext, ".pdf", StringComparison.OrdinalIgnoreCase))
            {
                var dest = Path.Combine(tempDir, Path.GetFileName(inputPath));
                File.Copy(inputPath, dest, true);
                return dest;
            }

            if (!SupportedExtensions.Contains(ext))
                throw new NotSupportedException(
                    string.Format("File format '{0}' is not supported. Supported: PDF, DOCX, XLSX, PPTX, CSV, PNG, JPG, BMP, GIF, TIFF, WebP.", ext));

            return ConvertToPdf(inputPath, tempDir);
        }

        private static string ConvertToPdf(string inputPath, string outputDir)
        {
            var soffice    = FindSoffice();
            var profileDir = Path.Combine(Path.GetTempPath(), "ixp_lo_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(profileDir);

            try
            {
                var profileUri = new Uri(profileDir).AbsoluteUri;
                var args = string.Format(
                    "--headless \"-env:UserInstallation={0}\" --convert-to pdf --outdir \"{1}\" \"{2}\"",
                    profileUri, outputDir, inputPath);

                var psi = new ProcessStartInfo
                {
                    FileName               = soffice,
                    Arguments              = args,
                    RedirectStandardOutput = true,
                    RedirectStandardError  = true,
                    UseShellExecute        = false,
                    CreateNoWindow         = true,
                };

                using (var proc = Process.Start(psi))
                {
                    proc.WaitForExit(120000);

                    if (proc.ExitCode != 0)
                    {
                        var err = proc.StandardError.ReadToEnd();
                        throw new InvalidOperationException("LibreOffice conversion failed: " + err);
                    }
                }

                var stem   = Path.GetFileNameWithoutExtension(inputPath);
                var output = Path.Combine(outputDir, stem + ".pdf");

                if (!File.Exists(output) || new FileInfo(output).Length == 0)
                    throw new InvalidOperationException(
                        "LibreOffice produced no output. File may be corrupted or password-protected.");

                return output;
            }
            finally
            {
                try { Directory.Delete(profileDir, true); } catch { }
            }
        }

        private static string FindSoffice()
        {
            var envPath = Environment.GetEnvironmentVariable("LIBREOFFICE_PATH");
            if (!string.IsNullOrEmpty(envPath) && File.Exists(envPath))
                return envPath;

            // Windows paths
            foreach (var path in WindowsPaths)
                if (File.Exists(path)) return path;

            // Try PATH (works for both Windows soffice.exe and Linux soffice)
            foreach (var bin in new[] { "soffice.exe", "soffice", "libreoffice" })
            {
                var which = FindInPath(bin);
                if (which != null) return which;
            }

            throw new InvalidOperationException(
                "LibreOffice (soffice) was not found on this machine.\n\n" +
                "  Windows: winget install TheDocumentFoundation.LibreOffice\n" +
                "  Linux:   apt-get install -y libreoffice\n\n" +
                "After installation, restart Studio or the robot process.\n" +
                "Or set the LIBREOFFICE_PATH environment variable to the soffice binary path.");
        }

        private static string FindInPath(string binary)
        {
            var pathVar = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
            foreach (var dir in pathVar.Split(Path.PathSeparator))
            {
                var full = Path.Combine(dir, binary);
                if (File.Exists(full)) return full;
            }
            return null;
        }
    }
}
