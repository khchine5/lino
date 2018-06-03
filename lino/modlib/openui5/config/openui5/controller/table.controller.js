sap.ui.define([
   "lino/controller/baseController",
	"sap/ui/model/json/JSONModel",
	"sap/ui/unified/Menu",
	"sap/ui/unified/MenuItem",
	"sap/m/MessageToast",
	"sap/ui/core/format/DateFormat"
], function(baseController, JSONModel, Menu, MenuItem, MessageToast, DateFormat) {
	"use strict";

	return baseController.extend("lino.controller.table", {

        log_rows: function(sMsg){
            console.log(sMsg,
                        this._table.getVisibleRowCount())
        },

		onInit : function () {
		    var me = this;
			var oView = this.getView();
			var oMainTable = this.getView().byId("MAIN_TABLE");
			this._is_rendered = false
            this._table = oMainTable
			this.page_limit = this.visibleRowCount;
            this._PK = oMainTable.data("PK");
            this._actor_id = oMainTable.data("actor_id");
            this._content_type = oMainTable.data("content_type"); // null or int
            this._is_slave = oMainTable.data("is_slave"); // null or int

            this._table.setBusy(true);

            this._table.addEventDelegate({
                afterRendering: function(){
                    me.log_rows("tableAfterRender");
                }
            });

            // override after rendering event handler to find out how many rows are rendered and how many should be per page
            // Is run twice on inital loading of view, second time has the correct values
            // view after render event is fired after first firing of this event, but before second firing of table event
            this._table.onAfterRendering = function(){
                sap.ui.table.Table.prototype.onAfterRendering.apply(this, arguments);
                me.reload.apply(me, arguments);
            };

			// Set values for table conf
			oView.setModel(new JSONModel({
//				showVisibilityMenuEntry: false,
				showFreezeMenuEntry: false,
				enableCellFilter: false
			}), "ui");

			// Set meta data for table/actor
			oView.setModel(new JSONModel({
			    page : 1,
			    page_old: 1, // Todo: implement correctly for setting on invalid page number value
                page_total : "N/A"
			}), "meta");

			// Param values (unused ATM)
			oView.setModel(new JSONModel({
			}), "pv");



		},

        onAfterRendering : function(oEvent){
            // to prevent second loading of data on init,
            this._is_rendered = true;

        },
        reload : function(oEvent){
         // Fetches the page that's set in {meta>page} or if that's not a valid page page_old
         // Called on page-resize and load, after the table has rendered and knows it's row count.
         // oEvent is from table afterendering event
            this._table.setBusy(true);
            this.page_limit = this._table.getVisibleRowCount();
                if (this._is_rendered){
                        var oJSONModel = this.initSampleDataModel();
                        this.getView().setModel(oJSONModel);
                    }

        },

//        beforeExit: function(){console.log("beforeExit")},


		initSampleDataModel : function() {
		    var me = this
			this._table.setBusy(true);
			var oRecordDataModel = new JSONModel();
			var oModel =me.getView().getModel("meta");
            var data = {limit:this.page_limit,
                        fmt:'json',
                        mt:this._content_type,
                        start: (oModel.getProperty("/page") - 1) * this.page_limit }
			var oDateFormat = DateFormat.getDateInstance({source: {pattern: "timestamp"}, pattern: "dd/MM/yyyy"});
            if (this._is_slave){
                data.mk = this.getParentView().getController()._PK
            }

			jQuery.ajax(this.getView().byId("MAIN_TABLE").data("url"), {
				dataType: "json",
				data:data,
				success: function (oData) {
				    var iPage = Math.ceil(oData.count / me.page_limit);
				    oModel.setProperty("/page_total", iPage);
				    oModel.setProperty("/page_old", iPage);

				    oRecordDataModel.setData(oData);
					me._table.setBusy(false)
				},
				error: function () {
					jQuery.sap.log.error("failed to load json");
				}
			});

			return oRecordDataModel;
		},


		onRowNavPress : function(oEvent) {
		    // todo refactor into open_window method of app controller
		    var oRow = oEvent.getParameter("row");
            var oBindingContext = oRow.getBindingContext();
			var oItem = oEvent.getParameter("item");
			var record_id = this.getView().getModel().getProperty(this._PK, oBindingContext);
			console.log("Opening detail for: " +  this._actor_id  + "/" + record_id);

            var msg = "'" + oEvent.getParameter("item").getText() + this._actor_id +":" + "detail" + "' pressed";
			MessageToast.show(msg);

			this.routeTo("detail", this._actor_id,{"record_id":record_id});

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

        // Unused, from ui5 sample docs
		showInfo : function(oEvent) {
			try {
				jQuery.sap.require("sap.ui.table.sample.TableExampleUtils");
				sap.ui.table.sample.TableExampleUtils.showInfo(jQuery.sap.getModulePath("sap.ui.table.sample.Menus", "/info.json"), oEvent.getSource());
			} catch (e) {
				// nothing
			}
		},

        // Todo disable prev and first on first page, and next and last on last page.
		onFirstPress: function(oEvent){
            var oModel = this.getView().getModel("meta");
            oModel.setProperty("/page", 1);
            this.reload();
		},
        onPrevPress: function(oEvent){
            var oModel = this.getView().getModel("meta");
            oModel.setProperty("/page", Math.max( 1 ,oModel.getProperty("/page") - 1) );
            this.reload();
        },
        onPagerInputChange: function(oEvent){
            var oModel = this.getView().getModel("meta");
            var sPage  = +oEvent.getParameters().value; //+ converts value into int or NaN // value is same as {meta>page}
            var sOldPage = oModel.getProperty("/page_old");
            var input = oEvent.getSource();
            console.log(sPage, sOldPage, input)
            if (sPage!=sOldPage){
                input.setValueState("None");
                MessageToast.show("Should load page:"+sPage)
                this.reload()
                }
            else if (isNaN(sPage)){
                input.setValueState("Error");
            }
        },
        onNextPress: function(oEvent){
            var oModel = this.getView().getModel("meta");
            oModel.setProperty("/page", Math.min(oModel.getProperty("/page")+1, oModel.getProperty("/page_total")))
            this.reload();
        },
        onLastPress: function(oEvent){
            var oModel = this.getView().getModel("meta");
            oModel.setProperty("/page", oModel.getProperty("/page_total"))
            this.reload();
        }

	});

});