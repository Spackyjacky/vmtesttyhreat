import SwiftUI
import SwiftData

struct StockView: View {
    @Query(sort: \Product.name) private var products: [Product]
    @State private var adjustingProduct: Product?
    @State private var showLowStockOnly = false

    private var filtered: [Product] {
        showLowStockOnly ? products.filter { $0.isLowStock } : products
    }

    var body: some View {
        List {
            ForEach(filtered) { product in
                Button {
                    adjustingProduct = product
                } label: {
                    HStack {
                        VStack(alignment: .leading) {
                            Text(product.name)
                            Text("SKU: \(product.sku)").font(.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text("\(product.stockQuantity)")
                            .font(.title3.bold())
                            .foregroundStyle(product.isLowStock ? .red : .primary)
                    }
                }
                .buttonStyle(.plain)
            }
        }
        .navigationTitle("Stock")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Toggle("Low stock only", isOn: $showLowStockOnly)
            }
        }
        .sheet(item: $adjustingProduct) { product in
            StockAdjustmentSheet(product: product)
        }
    }
}
