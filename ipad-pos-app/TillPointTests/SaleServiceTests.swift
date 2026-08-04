import XCTest
import SwiftData
@testable import TillPoint

@MainActor
final class SaleServiceTests: XCTestCase {
    private func makeInMemoryContext() throws -> ModelContext {
        let schema = Schema([Product.self, Category.self, Sale.self, SaleLineItem.self, StockAdjustment.self, TillSession.self, AppSettings.self])
        let configuration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: true)
        let container = try ModelContainer(for: schema, configurations: [configuration])
        return ModelContext(container)
    }

    func testCompleteSaleDecrementsStockAndComputesTotals() throws {
        let context = try makeInMemoryContext()
        let product = Product(name: "Widget", sku: "WID-1", priceCents: 1200, stockQuantity: 10, taxRatePercent: 20)
        context.insert(product)

        let saleService = SaleService(modelContext: context)
        let sale = saleService.completeSale(
            cartItems: [CartItem(product: product, quantity: 3)],
            paymentMethod: .cash,
            cashTenderedCents: 4000,
            operatorName: "Alex",
            customerEmail: nil
        )

        XCTAssertEqual(product.stockQuantity, 7)
        XCTAssertEqual(sale.totalCents, 3600)
        XCTAssertEqual(sale.changeDueCents, 400)
        XCTAssertEqual(sale.lineItems?.count, 1)
    }

    func testVoidRestoresStockViaAdjustment() throws {
        let context = try makeInMemoryContext()
        let product = Product(name: "Widget", sku: "WID-1", priceCents: 1000, stockQuantity: 5)
        context.insert(product)

        let stockService = StockService(modelContext: context)
        stockService.adjustStock(for: product, delta: -2, reason: .sale)
        XCTAssertEqual(product.stockQuantity, 3)

        stockService.adjustStock(for: product, delta: 2, reason: .returned)
        XCTAssertEqual(product.stockQuantity, 5)
    }
}
