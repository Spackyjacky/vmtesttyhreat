import Foundation
import SwiftData

@Model
final class StockAdjustment {
    var id: UUID = UUID()
    var productId: UUID = UUID()
    var productName: String = ""
    var delta: Int = 0
    var reasonRaw: String = StockAdjustmentReason.manualCorrection.rawValue
    var note: String?
    var date: Date = Date()
    var resultingStockQuantity: Int = 0

    var reason: StockAdjustmentReason {
        get { StockAdjustmentReason(rawValue: reasonRaw) ?? .manualCorrection }
        set { reasonRaw = newValue.rawValue }
    }

    init(productId: UUID, productName: String, delta: Int, reason: StockAdjustmentReason, note: String? = nil, resultingStockQuantity: Int) {
        self.id = UUID()
        self.productId = productId
        self.productName = productName
        self.delta = delta
        self.reasonRaw = reason.rawValue
        self.note = note
        self.date = Date()
        self.resultingStockQuantity = resultingStockQuantity
    }
}
