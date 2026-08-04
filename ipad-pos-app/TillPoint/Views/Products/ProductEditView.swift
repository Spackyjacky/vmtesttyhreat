import SwiftUI
import SwiftData

struct ProductEditView: View {
    let product: Product?

    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss
    @Query(sort: \Category.name) private var categories: [Category]
    @Query private var allProducts: [Product]

    @State private var name = ""
    @State private var sku = ""
    @State private var barcode = ""
    @State private var priceText = ""
    @State private var costText = ""
    @State private var stockQuantityText = ""
    @State private var lowStockThresholdText = "5"
    @State private var taxRateText = "20"
    @State private var selectedCategory: Category?
    @State private var showBarcodeSheet = false
    @State private var showScanner = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Details") {
                    TextField("Product name", text: $name)
                    TextField("SKU", text: $sku)
                    Picker("Category", selection: $selectedCategory) {
                        Text("None").tag(Category?.none)
                        ForEach(categories) { category in
                            Text(category.name).tag(Category?.some(category))
                        }
                    }
                }

                Section("Barcode") {
                    HStack {
                        TextField("Barcode", text: $barcode)
                        Button("Scan") { showScanner = true }
                    }
                    if barcode.isEmpty {
                        Button("Generate Barcode") { generateBarcode() }
                    } else {
                        Button("View / Print Label") { showBarcodeSheet = true }
                    }
                }

                Section("Pricing") {
                    HStack {
                        Text("Price")
                        TextField("0.00", text: $priceText).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                    }
                    HStack {
                        Text("Cost")
                        TextField("0.00", text: $costText).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                    }
                    HStack {
                        Text("Tax rate %")
                        TextField("20", text: $taxRateText).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                    }
                }

                Section("Stock") {
                    HStack {
                        Text("Quantity in stock")
                        TextField("0", text: $stockQuantityText).keyboardType(.numberPad).multilineTextAlignment(.trailing)
                    }
                    HStack {
                        Text("Low stock alert threshold")
                        TextField("5", text: $lowStockThresholdText).keyboardType(.numberPad).multilineTextAlignment(.trailing)
                    }
                }

                if product != nil {
                    Section {
                        Button("Delete Product", role: .destructive) { deleteAndDismiss() }
                    }
                }
            }
            .navigationTitle(product == nil ? "New Product" : "Edit Product")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save() }
                        .disabled(name.isEmpty || priceText.isEmpty)
                }
            }
            .onAppear(perform: populateFromExistingProduct)
            .sheet(isPresented: $showBarcodeSheet) {
                BarcodeLabelSheet(code: barcode, productName: name)
            }
            .sheet(isPresented: $showScanner) {
                NavigationStack {
                    CameraBarcodeScannerView { code in
                        barcode = code
                        showScanner = false
                    }
                    .navigationTitle("Scan Barcode")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Cancel") { showScanner = false }
                        }
                    }
                }
            }
        }
    }

    private func populateFromExistingProduct() {
        guard let product else { return }
        name = product.name
        sku = product.sku
        barcode = product.barcode ?? ""
        priceText = String(format: "%.2f", Double(product.priceCents) / 100)
        costText = String(format: "%.2f", Double(product.costCents) / 100)
        stockQuantityText = String(product.stockQuantity)
        lowStockThresholdText = String(product.lowStockThreshold)
        taxRateText = String(product.taxRatePercent)
        selectedCategory = product.category
    }

    private func generateBarcode() {
        let existingCodes = Set(allProducts.compactMap { $0.barcode })
        barcode = BarcodeGenerator.randomUniqueBarcode { existingCodes.contains($0) }
    }

    private func save() {
        let priceCents = Int(((Double(priceText) ?? 0) * 100).rounded())
        let costCents = Int(((Double(costText) ?? 0) * 100).rounded())
        let stockQuantity = Int(stockQuantityText) ?? 0
        let lowStockThreshold = Int(lowStockThresholdText) ?? 5
        let taxRate = Double(taxRateText) ?? 0

        if let product {
            product.name = name
            product.sku = sku
            product.barcode = barcode.isEmpty ? nil : barcode
            product.priceCents = priceCents
            product.costCents = costCents
            product.stockQuantity = stockQuantity
            product.lowStockThreshold = lowStockThreshold
            product.taxRatePercent = taxRate
            product.category = selectedCategory
        } else {
            let newProduct = Product(
                name: name,
                sku: sku,
                barcode: barcode.isEmpty ? nil : barcode,
                priceCents: priceCents,
                costCents: costCents,
                stockQuantity: stockQuantity,
                lowStockThreshold: lowStockThreshold,
                taxRatePercent: taxRate,
                category: selectedCategory
            )
            modelContext.insert(newProduct)
        }

        try? modelContext.save()
        dismiss()
    }

    private func deleteAndDismiss() {
        guard let product else { return }
        modelContext.delete(product)
        try? modelContext.save()
        dismiss()
    }
}
