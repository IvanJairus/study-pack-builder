import Foundation
import Vision
import AppKit

let arguments = CommandLine.arguments
guard arguments.count > 1 else {
    fputs("usage: ocr_vision.swift <image>\n", stderr)
    exit(2)
}
let path = arguments[1]
guard let image = NSImage(contentsOfFile: path),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fputs("cannot load \(path)\n", stderr)
    exit(1)
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["id-ID", "en-US"]
let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    fputs("ocr failed: \(error)\n", stderr)
    exit(2)
}
for observation in request.results ?? [] {
    guard let candidate = observation.topCandidates(1).first else { continue }
    let box = observation.boundingBox
    print(String(format: "%.4f\t%.4f\t%.4f\t%.4f\t%@", box.origin.x, box.origin.y, box.width, box.height, candidate.string))
}
