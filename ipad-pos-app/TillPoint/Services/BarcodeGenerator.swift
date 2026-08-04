import CoreImage
import UIKit

enum BarcodeGenerator {
    static func code128Image(from string: String, targetSize: CGSize = CGSize(width: 300, height: 120)) -> UIImage? {
        guard !string.isEmpty else { return nil }
        guard let filter = CIFilter(name: "CICode128BarcodeGenerator") else { return nil }
        let data = Data(string.utf8)
        filter.setValue(data, forKey: "inputMessage")
        filter.setValue(0, forKey: "inputQuietSpace")
        guard let outputImage = filter.outputImage else { return nil }

        let scaleX = targetSize.width / outputImage.extent.width
        let scaleY = targetSize.height / outputImage.extent.height
        let transformed = outputImage.transformed(by: CGAffineTransform(scaleX: scaleX, y: scaleY))

        let context = CIContext()
        guard let cgImage = context.createCGImage(transformed, from: transformed.extent) else { return nil }
        return UIImage(cgImage: cgImage)
    }

    /// Generates a unique in-store barcode following the GS1 "restricted circulation"
    /// number range (prefix 20-29), suitable for products with no manufacturer barcode.
    static func randomUniqueBarcode(existing: (String) -> Bool) -> String {
        var candidate: String
        repeat {
            let randomDigits = (0..<11).map { _ in String(Int.random(in: 0...9)) }.joined()
            let base = "2" + randomDigits
            candidate = base + String(ean13CheckDigit(for: base))
        } while existing(candidate)
        return candidate
    }

    private static func ean13CheckDigit(for twelveDigits: String) -> Int {
        let digits = twelveDigits.compactMap { $0.wholeNumberValue }
        guard digits.count == 12 else { return 0 }
        let sum = digits.enumerated().reduce(0) { partial, item in
            let (index, digit) = item
            return partial + digit * (index % 2 == 0 ? 1 : 3)
        }
        let mod = sum % 10
        return mod == 0 ? 0 : 10 - mod
    }
}
