import Foundation
import SwiftData

@MainActor
final class StockService {
    let modelContext: ModelContext
    init(modelContext: ModelContext) { self.modelContext = modelContext }

    func adjustStock(for product: Product, delta: Int, reason: StockAdjustmentReason, note: String? = nil) {
        product.stockQuantity += delta
        let adjustment = StockAdjustment(
            productId: product.id,
            productName: product.name,
            delta: delta,
            reason: reason,
            note: note,
            resultingStockQuantity: product.stockQuantity
        )
        modelContext.insert(adjustment)
        try? modelContext.save()
    }
}

@MainActor
final class SaleService {
    let modelContext: ModelContext
    let stockService: StockService

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
        self.stockService = StockService(modelContext: modelContext)
    }

    func completeSale(
        cartItems: [CartItem],
        paymentMethod: PaymentMethod,
        cashTenderedCents: Int?,
        operatorName: String?,
        customerEmail: String?
    ) -> Sale {
        let receiptNumber = Self.generateReceiptNumber()
        let sale = Sale(receiptNumber: receiptNumber, paymentMethod: paymentMethod, operatorName: operatorName)

        var subtotal = 0
        var tax = 0
        var lineItems: [SaleLineItem] = []

        for cartItem in cartItems {
            let product = cartItem.product
            let unitTax = product.taxCentsForUnit
            let lineItem = SaleLineItem(
                productId: product.id,
                productName: product.name,
                sku: product.sku,
                quantity: cartItem.quantity,
                unitPriceCents: product.priceCents,
                taxCents: unitTax
            )
            lineItem.sale = sale
            lineItems.append(lineItem)
            subtotal += lineItem.lineTotalCents - (unitTax * cartItem.quantity)
            tax += unitTax * cartItem.quantity

            stockService.adjustStock(for: product, delta: -cartItem.quantity, reason: .sale, note: "Sale \(receiptNumber)")
        }

        sale.lineItems = lineItems
        sale.subtotalCents = subtotal
        sale.taxCents = tax
        sale.totalCents = subtotal + tax
        sale.customerEmail = customerEmail

        if paymentMethod == .cash, let tendered = cashTenderedCents {
            sale.cashTenderedCents = tendered
            sale.changeDueCents = max(0, tendered - sale.totalCents)
        }

        modelContext.insert(sale)
        try? modelContext.save()
        return sale
    }

    static func generateReceiptNumber() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyMMdd-HHmmss"
        return formatter.string(from: Date()) + "-" + String(Int.random(in: 100...999))
    }
}
