import SwiftUI

struct ProductGridView: View {
    let products: [Product]
    let onSelect: (Product) -> Void

    private let columns = [GridItem(.adaptive(minimum: 150, maximum: 200), spacing: 12)]

    var body: some View {
        ScrollView {
            LazyVGrid(columns: columns, spacing: 12) {
                ForEach(products) { product in
                    Button {
                        onSelect(product)
                    } label: {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(product.name)
                                .font(.headline)
                                .lineLimit(2)
                                .multilineTextAlignment(.leading)
                            Text(CurrencyFormatter.string(fromCents: product.priceCents))
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            Text(product.isLowStock ? "Stock: \(product.stockQuantity) \u{26A0}\u{FE0F}" : "Stock: \(product.stockQuantity)")
                                .font(.caption2)
                                .foregroundStyle(product.isLowStock ? .red : .secondary)
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color(.secondarySystemBackground))
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding()
        }
    }
}
