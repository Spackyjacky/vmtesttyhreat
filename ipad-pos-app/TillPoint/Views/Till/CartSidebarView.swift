import SwiftUI

struct CartSidebarView: View {
    @Binding var cart: [CartItem]
    let subtotalCents: Int
    let currencyCode: String
    let onCheckout: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Text("Current Sale")
                .font(.title2.bold())
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()

            if cart.isEmpty {
                Spacer()
                Text("Cart is empty").foregroundStyle(.secondary)
                Spacer()
            } else {
                List {
                    ForEach(cart) { item in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(item.product.name).font(.subheadline)
                                Text(CurrencyFormatter.string(fromCents: item.product.priceCents, currencyCode: currencyCode))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Stepper(value: quantityBinding(for: item), in: 1...999) {
                                Text("\(item.quantity)")
                            }
                            .fixedSize()
                            Text(CurrencyFormatter.string(fromCents: item.lineTotalCents, currencyCode: currencyCode))
                                .frame(width: 70, alignment: .trailing)
                        }
                    }
                    .onDelete { indices in
                        cart.remove(atOffsets: indices)
                    }
                }
                .listStyle(.plain)
            }

            Divider()

            VStack(spacing: 12) {
                HStack {
                    Text("Total").font(.title3.bold())
                    Spacer()
                    Text(CurrencyFormatter.string(fromCents: subtotalCents, currencyCode: currencyCode))
                        .font(.title3.bold())
                }

                Button {
                    onCheckout()
                } label: {
                    Text("Charge")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding()
                }
                .buttonStyle(.borderedProminent)
                .disabled(cart.isEmpty)
            }
            .padding()
        }
    }

    private func quantityBinding(for item: CartItem) -> Binding<Int> {
        Binding(
            get: { item.quantity },
            set: { newValue in
                if let index = cart.firstIndex(where: { $0.id == item.id }) {
                    cart[index].quantity = max(1, newValue)
                }
            }
        )
    }
}
