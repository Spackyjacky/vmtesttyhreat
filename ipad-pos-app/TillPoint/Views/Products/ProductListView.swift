import SwiftUI
import SwiftData

struct ProductListView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Product.name) private var products: [Product]
    @State private var searchText = ""
    @State private var editingProduct: Product?
    @State private var showNewProduct = false

    private var filtered: [Product] {
        guard !searchText.isEmpty else { return products }
        return products.filter {
            $0.name.localizedCaseInsensitiveContains(searchText) ||
            $0.sku.localizedCaseInsensitiveContains(searchText) ||
            ($0.barcode?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }

    var body: some View {
        List {
            ForEach(filtered) { product in
                Button {
                    editingProduct = product
                } label: {
                    HStack {
                        VStack(alignment: .leading) {
                            Text(product.name).foregroundStyle(.primary)
                            Text("SKU: \(product.sku)  \u{2022}  \(product.barcode ?? "No barcode")")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        VStack(alignment: .trailing) {
                            Text(CurrencyFormatter.string(fromCents: product.priceCents))
                            Text("Stock: \(product.stockQuantity)")
                                .font(.caption)
                                .foregroundStyle(product.isLowStock ? .red : .secondary)
                        }
                    }
                }
                .buttonStyle(.plain)
            }
            .onDelete(perform: deleteProducts)
        }
        .searchable(text: $searchText, prompt: "Search products")
        .navigationTitle("Products")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showNewProduct = true
                } label: {
                    Label("Add Product", systemImage: "plus")
                }
            }
        }
        .sheet(item: $editingProduct) { product in
            ProductEditView(product: product)
        }
        .sheet(isPresented: $showNewProduct) {
            ProductEditView(product: nil)
        }
    }

    private func deleteProducts(at offsets: IndexSet) {
        for index in offsets {
            modelContext.delete(filtered[index])
        }
        try? modelContext.save()
    }
}
