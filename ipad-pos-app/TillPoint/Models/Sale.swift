import Foundation
import SwiftData

@Model
final class Sale {
    var id: UUID = UUID()
    var receiptNumber: String = ""
    var date: Date = Date()

    @Relationship(deleteRule: .cascade, inverse: \SaleLineItem.sale)
    var lineItems: [SaleLineItem]? = []

    var subtotalCents: Int = 0
    var taxCents: Int = 0
    var totalCents: Int = 0

    var paymentMethodRaw: String = PaymentMethod.cash.rawValue
    var cashTenderedCents: Int?
    var changeDueCents: Int?

    var customerEmail: String?
    var receiptEmailedAt: Date?

    var statusRaw: String = SaleStatus.completed.rawValue
    var operatorName: String?

    var paymentMethod: PaymentMethod {
        get { PaymentMethod(rawValue: paymentMethodRaw) ?? .cash }
        set { paymentMethodRaw = newValue.rawValue }
    }

    var status: SaleStatus {
        get { SaleStatus(rawValue: statusRaw) ?? .completed }
        set { statusRaw = newValue.rawValue }
    }

    init(receiptNumber: String, paymentMethod: PaymentMethod, operatorName: String? = nil) {
        self.id = UUID()
        self.receiptNumber = receiptNumber
        self.date = Date()
        self.paymentMethodRaw = paymentMethod.rawValue
        self.statusRaw = SaleStatus.completed.rawValue
        self.operatorName = operatorName
    }
}
