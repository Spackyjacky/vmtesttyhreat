import SwiftUI
import SwiftData

struct StockAdjustmentSheet: View {
    let product: Product

    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    @State private var deltaText = ""
    @State private var reason: StockAdjustmentReason = .restock
    @State private var note = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Product") {
                    Text(product.name)
                    Text("Current stock: \(product.stockQuantity)").foregroundStyle(.secondary)
                }
                Section("Adjustment") {
                    TextField("Amount (+/-)", text: $deltaText)
                        .keyboardType(.numbersAndPunctuation)
                    Picker("Reason", selection: $reason) {
                        ForEach(StockAdjustmentReason.allCases) { r in
                            Text(r.displayName).tag(r)
                        }
                    }
                    TextField("Note (optional)", text: $note)
                }
            }
            .navigationTitle("Adjust Stock")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { applyAdjustment() }
                        .disabled(Int(deltaText) == nil)
                }
            }
        }
    }

    private func applyAdjustment() {
        guard let delta = Int(deltaText) else { return }
        let service = StockService(modelContext: modelContext)
        service.adjustStock(for: product, delta: delta, reason: reason, note: note.isEmpty ? nil : note)
        dismiss()
    }
}
