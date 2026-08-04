import SwiftUI
import SwiftData

struct SettingsView: View {
    @Environment(\.modelContext) private var modelContext
    @Query private var settingsList: [AppSettings]

    private var settings: AppSettings {
        if let existing = settingsList.first { return existing }
        let created = AppSettings()
        modelContext.insert(created)
        return created
    }

    var body: some View {
        Form {
            Section("Store Details") {
                TextField("Store name", text: bindingFor(\.storeName))
                TextField("Address line 1", text: bindingFor(\.addressLine1))
                TextField("Address line 2", text: bindingFor(\.addressLine2))
                TextField("Phone number", text: bindingFor(\.phoneNumber))
                TextField("VAT number", text: bindingFor(\.vatNumber))
            }

            Section("Receipt") {
                TextField("Footer message", text: bindingFor(\.receiptFooter))
                TextField("Email subject", text: bindingFor(\.receiptEmailSubject))
                Toggle("Auto-open cash drawer after sale", isOn: bindingFor(\.printerAutoOpenDrawer))
            }

            Section("Tax & Currency") {
                HStack {
                    Text("Default tax rate %")
                    Spacer()
                    TextField("20", value: bindingForDouble(\.defaultTaxRatePercent), format: .number)
                        .keyboardType(.decimalPad)
                        .multilineTextAlignment(.trailing)
                        .frame(width: 80)
                }
                Picker("Currency", selection: bindingFor(\.currencyCode)) {
                    Text("GBP (\u{00A3})").tag("GBP")
                    Text("USD ($)").tag("USD")
                    Text("EUR (\u{20AC})").tag("EUR")
                }
            }

            Section("Appearance") {
                Picker("Appearance", selection: appearanceBinding()) {
                    ForEach(AppAppearance.allCases) { option in
                        Text(option.displayName).tag(option)
                    }
                }
                .pickerStyle(.segmented)
            }

            Section("Hardware") {
                NavigationLink("Printer & Cash Drawer") { PrinterSetupView() }
            }

            Section("Categories") {
                NavigationLink("Manage Categories") { CategoryListView() }
            }

            Section("Till Session") {
                NavigationLink("Cashing Up") { TillSessionView() }
            }
        }
        .navigationTitle("Settings")
    }

    private func bindingFor(_ keyPath: ReferenceWritableKeyPath<AppSettings, String>) -> Binding<String> {
        Binding(get: { settings[keyPath: keyPath] }, set: { settings[keyPath: keyPath] = $0; try? modelContext.save() })
    }

    private func bindingFor(_ keyPath: ReferenceWritableKeyPath<AppSettings, Bool>) -> Binding<Bool> {
        Binding(get: { settings[keyPath: keyPath] }, set: { settings[keyPath: keyPath] = $0; try? modelContext.save() })
    }

    private func bindingForDouble(_ keyPath: ReferenceWritableKeyPath<AppSettings, Double>) -> Binding<Double> {
        Binding(get: { settings[keyPath: keyPath] }, set: { settings[keyPath: keyPath] = $0; try? modelContext.save() })
    }

    private func appearanceBinding() -> Binding<AppAppearance> {
        Binding(
            get: { settings.appearance },
            set: { settings.appearance = $0; try? modelContext.save() }
        )
    }
}
