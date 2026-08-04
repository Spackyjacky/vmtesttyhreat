import Foundation
import SwiftData

@Model
final class SaleLineItem {
    var id: UUID = UUID()
    var productId: UUID = UUID()
    var productName: String = ""
    var sku: String = ""
    var quantity: Int = 1
    var unitPriceCents: Int = 0
    var lineTotalCents: Int = 0
    var taxCents: Int = 0

    var sale: Sale?

    init(productId: UUID, productName: String, sku: String, quantity: Int, unitPriceCents: Int, taxCents: Int) {
        self.id = UUID()
        self.productId = productId
        self.productName = productName
        self.sku = sku
        self.quantity = quantity
        self.unitPriceCents = unitPriceCents
        self.lineTotalCents = unitPriceCents * quantity
        self.taxCents = taxCents * quantity
    }
}
