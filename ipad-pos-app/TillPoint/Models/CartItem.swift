import Foundation

struct CartItem: Identifiable {
    let id: UUID
    let product: Product
    var quantity: Int

    init(product: Product, quantity: Int = 1) {
        self.id = product.id
        self.product = product
        self.quantity = quantity
    }

    var lineTotalCents: Int { product.priceCents * quantity }
}
