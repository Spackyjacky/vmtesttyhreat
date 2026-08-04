import Foundation

enum StockReportScope {
    case all
    case lowStockOnly
}

enum StockReportExporter {
    /// Builds a CSV file for the given products and writes it to a temporary
    /// file, ready to hand to a share sheet (export, email, AirDrop, save to Files).
    static func exportCSV(products: [Product], scope: StockReportScope, currencyCode: String) -> URL? {
        let rows = scope == .lowStockOnly ? products.filter { $0.isLowStock } : products

        var csv = "Name,SKU,Barcode,Category,Price,Cost,Stock Quantity,Low Stock Threshold,Status\n"
        for product in rows.sorted(by: { $0.name < $1.name }) {
            let fields: [String] = [
                product.name,
                product.sku,
                product.barcode ?? "",
                product.category?.name ?? "",
                priceString(product.priceCents),
                priceString(product.costCents),
                "\(product.stockQuantity)",
                "\(product.lowStockThreshold)",
                product.isLowStock ? "LOW STOCK" : "OK"
            ]
            csv += fields.map(escapeCSVField).joined(separator: ",") + "\n"
        }

        let filenameSuffix = scope == .lowStockOnly ? "low-stock" : "all-stock"
        let dateStamp = DateFormatter.filenameStamp.string(from: Date())
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("stock-report-\(filenameSuffix)-\(dateStamp)")
            .appendingPathExtension("csv")

        do {
            try csv.write(to: url, atomically: true, encoding: .utf8)
            return url
        } catch {
            return nil
        }
    }

    private static func priceString(_ cents: Int) -> String {
        String(format: "%.2f", Double(cents) / 100)
    }

    private static func escapeCSVField(_ field: String) -> String {
        guard field.contains(",") || field.contains("\"") || field.contains("\n") else { return field }
        return "\"" + field.replacingOccurrences(of: "\"", with: "\"\"") + "\""
    }
}

private extension DateFormatter {
    static let filenameStamp: DateFormatter = {
        let df = DateFormatter()
        df.dateFormat = "yyyy-MM-dd-HHmm"
        return df
    }()
}
