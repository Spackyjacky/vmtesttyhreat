import Foundation
import SwiftData

@Model
final class TillSession {
    var id: UUID = UUID()
    var openedAt: Date = Date()
    var closedAt: Date?
    var openingFloatCents: Int = 0
    var closingCountedCents: Int?
    var operatorName: String = ""
    var isOpen: Bool = true
    var notes: String?

    init(openingFloatCents: Int, operatorName: String) {
        self.id = UUID()
        self.openedAt = Date()
        self.openingFloatCents = openingFloatCents
        self.operatorName = operatorName
        self.isOpen = true
    }
}
