import Foundation
import SwiftData

@Model
final class Category {
    var id: UUID = UUID()
    var name: String = ""
    var colorHex: String = "#4A90D9"
    var sortOrder: Int = 0

    @Relationship(deleteRule: .nullify, inverse: \Product.category)
    var products: [Product]? = []

    init(name: String, colorHex: String = "#4A90D9", sortOrder: Int = 0) {
        self.id = UUID()
        self.name = name
        self.colorHex = colorHex
        self.sortOrder = sortOrder
    }
}
