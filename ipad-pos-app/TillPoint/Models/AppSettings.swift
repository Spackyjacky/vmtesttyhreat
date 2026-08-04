import Foundation
import SwiftData

@Model
final class AppSettings {
    var id: UUID = UUID()
    var storeName: String = "My Store"
    var addressLine1: String = ""
    var addressLine2: String = ""
    var phoneNumber: String = ""
    var vatNumber: String = ""
    var receiptFooter: String = "Thank you for shopping with us!"
    var defaultTaxRatePercent: Double = 20.0
    var currencyCode: String = "GBP"
    var lastConnectedPrinterId: String?
    var printerAutoOpenDrawer: Bool = true
    var receiptEmailSubject: String = "Your Receipt"
    var appearanceRaw: String = AppAppearance.system.rawValue

    var appearance: AppAppearance {
        get { AppAppearance(rawValue: appearanceRaw) ?? .system }
        set { appearanceRaw = newValue.rawValue }
    }

    init() {
        self.id = UUID()
    }
}
