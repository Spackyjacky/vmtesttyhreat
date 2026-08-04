import Foundation
import SwiftUI

enum PaymentMethod: String, Codable, CaseIterable, Identifiable {
    case cash
    case card
    case other

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .cash: return "Cash"
        case .card: return "Card"
        case .other: return "Other"
        }
    }
}

enum AppAppearance: String, Codable, CaseIterable, Identifiable {
    case system
    case light
    case dark

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .system: return "System"
        case .light: return "Light"
        case .dark: return "Dark"
        }
    }

    var colorScheme: ColorScheme? {
        switch self {
        case .system: return nil
        case .light: return .light
        case .dark: return .dark
        }
    }
}

enum SaleStatus: String, Codable {
    case completed
    case refunded
    case voided
}

enum StockAdjustmentReason: String, Codable, CaseIterable, Identifiable {
    case restock
    case sale
    case manualCorrection
    case stockTake
    case damaged
    case returned

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .restock: return "Restock"
        case .sale: return "Sale"
        case .manualCorrection: return "Manual Correction"
        case .stockTake: return "Stock Take"
        case .damaged: return "Damaged / Written Off"
        case .returned: return "Customer Return"
        }
    }
}
