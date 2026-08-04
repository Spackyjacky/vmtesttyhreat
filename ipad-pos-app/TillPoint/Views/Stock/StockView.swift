import SwiftUI
import SwiftData

struct StockView: View {
    @Query(sort: \Product.name) private var products: [Product]
    @Query private var settingsList: [AppSettings]
    @State private var adjustingProduct: Product?
    @State private var showLowStockOnly = false
    @State private var showExportOptions = false
    @State private var exportFileURL: URL?

    private var settings: AppSettings { settingsList.first ?? AppSettings() }

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
                Button {
                    showExportOptions = true
                } label: {
                    Label("Export Report", systemImage: "square.and.arrow.up")
                }
            }
            ToolbarItem(placement: .primaryAction) {
                Toggle("Low stock only", isOn: $showLowStockOnly)
            }
        }
        .confirmationDialog("Export Stock Report", isPresented: $showExportOptions, titleVisibility: .visible) {
            Button("All Stock") { export(scope: .all) }
            Button("Low Stock Items Only") { export(scope: .lowStockOnly) }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Choose what to include in the CSV report.")
        }
        .sheet(isPresented: Binding(get: { exportFileURL != nil }, set: { if !$0 { exportFileURL = nil } })) {
            if let exportFileURL {
                ShareSheet(items: [exportFileURL])
            }
        }
        .sheet(item: $adjustingProduct) { product in
            StockAdjustmentSheet(product: product)
        }
    }

    private func export(scope: StockReportScope) {
        exportFileURL = StockReportExporter.exportCSV(products: products, scope: scope, currencyCode: settings.currencyCode)
    }
}
