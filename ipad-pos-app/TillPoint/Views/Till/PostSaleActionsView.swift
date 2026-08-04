import SwiftUI

struct PostSaleActionsView: View {
    let sale: Sale
    let settings: AppSettings
    let onDone: () -> Void

    @EnvironmentObject private var printerManager: BluetoothPrinterManager
    @State private var showEmailComposer = false
    @State private var emailAddress = ""
    @State private var showEmailPrompt = false

    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "checkmark.circle.fill")
                .resizable()
                .frame(width: 64, height: 64)
                .foregroundStyle(.green)

            Text("Sale Complete")
                .font(.title.bold())

            Text(CurrencyFormatter.string(fromCents: sale.totalCents, currencyCode: settings.currencyCode))
                .font(.system(size: 36, weight: .bold))

            if let change = sale.changeDueCents, change > 0 {
                Text("Change due: \(CurrencyFormatter.string(fromCents: change, currencyCode: settings.currencyCode))")
                    .font(.headline)
            }

            VStack(spacing: 12) {
                Button {
                    let bytes = ReceiptFormatter.escposReceipt(for: sale, settings: settings, openDrawer: false)
                    printerManager.printReceipt(bytes: bytes)
                } label: {
                    Label("Reprint Receipt", systemImage: "printer")
                        .frame(maxWidth: .infinity)
                        .padding()
                }
                .buttonStyle(.bordered)
                .disabled(printerManager.connectionState != .connected)

                Button {
                    printerManager.openCashDrawer()
                } label: {
                    Label("Open Cash Drawer", systemImage: "tray")
                        .frame(maxWidth: .infinity)
                        .padding()
                }
                .buttonStyle(.bordered)
                .disabled(printerManager.connectionState != .connected)

                Button {
                    showEmailPrompt = true
                } label: {
                    Label("Email Receipt", systemImage: "envelope")
                        .frame(maxWidth: .infinity)
                        .padding()
                }
                .buttonStyle(.bordered)
                .disabled(!MailComposerView.canSendMail())

                Button {
                    onDone()
                } label: {
                    Text("New Sale")
                        .frame(maxWidth: .infinity)
                        .padding()
                }
                .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal)
        }
        .padding()
        .alert("Email Receipt", isPresented: $showEmailPrompt) {
            TextField("Customer email", text: $emailAddress)
                .keyboardType(.emailAddress)
            Button("Send") { showEmailComposer = true }
            Button("Cancel", role: .cancel) {}
        }
        .sheet(isPresented: $showEmailComposer) {
            MailComposerView(
                recipient: emailAddress,
                subject: settings.receiptEmailSubject,
                body: ReceiptFormatter.plainTextReceipt(for: sale, settings: settings)
            )
        }
    }
}
