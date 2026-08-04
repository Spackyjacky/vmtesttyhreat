import SwiftUI
import SwiftData

struct TillView: View {
    @EnvironmentObject private var printerManager: BluetoothPrinterManager
    @Query(sort: \Product.name) private var products: [Product]
    @Query private var settingsList: [AppSettings]

    @State private var cart: [CartItem] = []
    @State private var searchText = ""
    @State private var showCheckout = false
    @State private var scanFeedback: String?

    private var settings: AppSettings { settingsList.first ?? AppSettings() }

    private var filteredProducts: [Product] {
        let active = products.filter { $0.isActive }
        guard !searchText.isEmpty else { return active }
        return active.filter {
            $0.name.localizedCaseInsensitiveContains(searchText) ||
            $0.sku.localizedCaseInsensitiveContains(searchText) ||
            ($0.barcode?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }

    private var subtotalCents: Int { cart.reduce(0) { $0 + $1.lineTotalCents } }

    var body: some View {
        HStack(spacing: 0) {
            VStack {
                TextField("Search products or scan barcode", text: $searchText)
                    .textFieldStyle(.roundedBorder)
                    .padding()

                if let scanFeedback {
                    Text(scanFeedback)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding(.bottom, 4)
                }

                ProductGridView(products: filteredProducts) { product in
                    addToCart(product)
                }
            }
            .frame(maxWidth: .infinity)

            Divider()

            CartSidebarView(
                cart: $cart,
                subtotalCents: subtotalCents,
                currencyCode: settings.currencyCode,
                onCheckout: { showCheckout = true }
            )
            .frame(width: 360)
        }
        .background(
            BarcodeScannerCaptureField(onScan: handleScan)
                .frame(width: 0, height: 0)
        )
        .sheet(isPresented: $showCheckout) {
            CheckoutSheet(cart: $cart, settings: settings)
                .environmentObject(printerManager)
        }
        .navigationTitle("Till")
    }

    private func addToCart(_ product: Product) {
        if let index = cart.firstIndex(where: { $0.product.id == product.id }) {
            cart[index].quantity += 1
        } else {
            cart.append(CartItem(product: product))
        }
        let remaining = product.stockQuantity - cartQuantity(for: product)
        scanFeedback = remaining <= 0 ? "Added \(product.name) \u{2014} low/no stock remaining" : "Added \(product.name)"
    }

    private func handleScan(_ code: String) {
        if let product = products.first(where: { $0.barcode == code }) {
            addToCart(product)
        } else {
            scanFeedback = "No product found for barcode \(code)"
        }
    }

    private func cartQuantity(for product: Product) -> Int {
        cart.first(where: { $0.product.id == product.id })?.quantity ?? 0
    }
}
