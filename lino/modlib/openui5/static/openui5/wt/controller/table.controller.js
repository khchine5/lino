sap.ui.define([
	"sap/ui/core/mvc/Controller",
	"sap/ui/model/json/JSONModel",
	"sap/ui/unified/Menu",
	"sap/ui/unified/MenuItem",
	"sap/m/MessageToast",
	"sap/ui/core/format/DateFormat"
], function(Controller, JSONModel, Menu, MenuItem, MessageToast, DateFormat) {
	"use strict";

	return Controller.extend("sap.ui.demo.wt.controller.table", {

		onInit : function () {
			var oView = this.getView();
            this._table = oView.byId("MAIN_TABLE")
			this.page_no = 0;
            this.page_limit = this.visibleRowCount;
            this.pv = []; // unused,
            this._PK = this.getView().byId("MAIN_TABLE").data("PK");
            this._actor_id = this.getView().byId("MAIN_TABLE").data("actor_id");

            if (this.count == undefined) this.count = 0;
			// set explored app's demo model on this sample
			var oJSONModel = this.initSampleDataModel();
			oView.setModel(oJSONModel);

			oView.setModel(new JSONModel({
//				showVisibilityMenuEntry: false,
				showFreezeMenuEntry: false,
				enableCellFilter: false
			}), "ui");
		},

        onNavButtonPress : function(oEvent){
            this.getNavport().back();
        },

		initSampleDataModel : function() {
			var oModel = new JSONModel();

			var oDateFormat = DateFormat.getDateInstance({source: {pattern: "timestamp"}, pattern: "dd/MM/yyyy"});

			jQuery.ajax(this.getView().byId("MAIN_TABLE").data("url"), {
				dataType: "json",
				data:{limit:15},
				success: function (oData) {
					oModel.setData(oData);
				},
				error: function () {
					jQuery.sap.log.error("failed to load json");
				}
			});
			console.log(this.count++)

			return oModel;
		},

		getNavport: function(){
		    var vp = sap.ui.getCore().byId("__component0---MAIN_VIEW").byId('viewport');
            return vp
		},


		onRowNavPress : function(oEvent) {
		    // todo refactor into open_window method of app controller
            var oRow = oEvent.getParameter("row");
            var oBindingContext = oRow.getBindingContext();
			var oItem = oEvent.getParameter("item");
			var sPk = this.getView().getModel().getProperty(this._PK, oBindingContext);
			console.log("Opening detail for: " +  this._actor_id  + "/" + sPk);


		    var oButton = oEvent.getSource();
            var actor_id = this._actor_id //oButton.data('actor_id');
            var action_name = "detail"// oButton.data('action_name');

			var msg = "'" + oEvent.getParameter("item").getText() + actor_id +":" + action_name + "' pressed";
			MessageToast.show(msg);
			var vp = this.getNavport(); //this.getView().byId('viewport')
			var content = sap.ui.getCore().byId("detail." + actor_id)
			if (content===undefined){
                content = new sap.ui.xmlview({id: "detail." + actor_id,
                                    viewName : "sap.ui.lino." + action_name + "." + actor_id});

                this.getView().addDependent(content)
			    vp.addPage(content);
			    }

			content.getController().load_record(sPk);
			vp.to(content);

		},


		onColumnSelect : function (oEvent) {
			var oCurrentColumn = oEvent.getParameter("column");
			var oImageColumn = this.getView().byId("image");
			if (oCurrentColumn === oImageColumn) {
				MessageToast.show("Column header " + oCurrentColumn.getLabel().getText() + " pressed.");
			}
		},

		onColumnMenuOpen: function (oEvent) {
			var oCurrentColumn = oEvent.getSource();
			var oImageColumn = this.getView().byId("image");
			if (oCurrentColumn != oImageColumn) {
				return;
			}

			//Just skip opening the column Menu on column "Image"
			oEvent.preventDefault();
		},

		onProductIdCellContextMenu : function (oEvent) {
			if (sap.ui.Device.support.touch) {
				return; //Do not use context menus on touch devices
			}

			if (oEvent.getParameter("columnId") != this.getView().createId("productId")) {
				return; //Custom context menu for product id column only
			}

			oEvent.preventDefault();

			var oRowContext = oEvent.getParameter("rowBindingContext");

			if (!this._oIdContextMenu) {
				this._oIdContextMenu = new Menu();
				this.getView().addDependent(this._oIdContextMenu);
			}

			this._oIdContextMenu.destroyItems();
			this._oIdContextMenu.addItem(new MenuItem({
				text: "My Custom Cell Action",
				select: function() {
					MessageToast.show("Context action triggered on Column 'Product ID' on id '" + oRowContext.getProperty("ProductId") + "'.");
				}
			}));

			//Open the menu on the cell
			var oCellDomRef = oEvent.getParameter("cellDomRef");
			var eDock = sap.ui.core.Popup.Dock;
			this._oIdContextMenu.open(false, oCellDomRef, eDock.BeginTop, eDock.BeginBottom, oCellDomRef, "none none");
		},

		onQuantityCustomItemSelect : function(oEvent) {
			MessageToast.show("Some custom action triggered on column 'Quantity'.");
		},

		onQuantitySort : function(oEvent) {
			var bAdd = oEvent.getParameter("ctrlKey") === true;
			var oColumn = this.getView().byId("quantity");
			var sOrder = oColumn.getSortOrder() == "Ascending" ? "Descending" : "Ascending";

			this.getView().byId("table").sort(oColumn, sOrder, bAdd);
		},

		showInfo : function(oEvent) {
			try {
				jQuery.sap.require("sap.ui.table.sample.TableExampleUtils");
				sap.ui.table.sample.TableExampleUtils.showInfo(jQuery.sap.getModulePath("sap.ui.table.sample.Menus", "/info.json"), oEvent.getSource());
			} catch (e) {
				// nothing
			}
		}

	});

});