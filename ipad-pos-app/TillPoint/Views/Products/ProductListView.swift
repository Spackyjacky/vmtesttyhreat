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
                            HStack(spacing: 6) {
                                Text(product.name).foregroundStyle(.primary)
                                if !product.showOnHomeScreen {
                                    Text("Scan only")
                                        .font(.caption2.bold())
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(Color.secondary.opacity(0.15))
                                        .clipShape(Capsule())
                                }
                            }
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
