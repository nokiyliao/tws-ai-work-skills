import AppKit
import Foundation
import Vision

func jsonString(_ object: Any) -> String {
    if let data = try? JSONSerialization.data(withJSONObject: object, options: []),
       let text = String(data: data, encoding: .utf8) {
        return text
    }
    return "[]"
}

var rows: [[String: Any]] = []

for arg in CommandLine.arguments.dropFirst() {
    let url = URL(fileURLWithPath: arg)
    var row: [String: Any] = ["path": arg, "text": ""]
    guard let image = NSImage(contentsOf: url),
          let tiff = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let cgImage = bitmap.cgImage else {
        row["error"] = "cannot load image"
        rows.append(row)
        continue
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["zh-Hant", "zh-Hans", "en-US"]

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do {
        try handler.perform([request])
        let observations = request.results ?? []
        let lines = observations.compactMap { obs in
            obs.topCandidates(1).first?.string
        }
        row["text"] = lines.joined(separator: "\n")
    } catch {
        row["error"] = "\(error)"
    }
    rows.append(row)
}

print(jsonString(rows))
