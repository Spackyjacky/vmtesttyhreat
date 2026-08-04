import Foundation
import SwiftData

@Model
final class Product {
    var id: UUID = UUID()
    var name: String = ""
    var sku: String = ""
    var barcode: String?
    var priceCents: Int = 0
    var costCents: Int = 0
    var stockQuantity: Int = 0
    var lowStockThreshold: Int = 5
    var taxRatePercent: Double = 0
    var isActive: Bool = true
    var createdAt: Date = Date()
    var notes: String?

    var category: Category?

    init(
        name: String,
        sku: String,
        barcode: String? = nil,
        priceCents: Int,
        costCents: Int = 0,
        stockQuantity: Int = 0,
        lowStockThreshold: Int = 5,
        taxRatePercent: Double = 0,
        category: Category? = nil
    ) {
        self.id = UUID()
        self.name = name
        self.sku = sku
        self.barcode = barcode
        self.priceCents = priceCents
        self.costCents = costCents
        self.stockQuantity = stockQuantity
        self.lowStockThreshold = lowStockThreshold
        self.taxRatePercent = taxRatePercent
        self.category = category
        self.createdAt = Date()
    }

    var isLowStock: Bool { stockQuantity <= lowStockThreshold }

    var priceDecimal: Decimal { Decimal(priceCents) / 100 }

    /// Tax portion of the (tax-inclusive) unit price, e.g. UK VAT-inclusive retail pricing.
    var taxCentsForUnit: Int {
        guard taxRatePercent > 0 else { return 0 }
        return Int((Double(priceCents) * taxRatePercent / (100 + taxRatePercent)).rounded())
    }
}
