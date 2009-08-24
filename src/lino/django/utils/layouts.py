## Copyright 2009 Luc Saffre

## This file is part of the Lino project.

## Lino is free software; you can redistribute it and/or modify it
## under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## Lino is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
## or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
## License for more details.

## You should have received a copy of the GNU General Public License
## along with Lino; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import traceback
import types

from django import forms
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.template.loader import render_to_string

EXT_CHAR_WIDTH = 9
EXT_CHAR_HEIGHT = 12

def py2js(v,k):
    if type(v) is types.BooleanType:
        return str(v).lower()
    #if k in ('width','labelWidth'):
    #    return str(v)+"*CHAR_WIDTH"
    return repr(v)
            
class js_code:
    "A string that py2js will represent as is, not between quotes."
    def __init__(self,s):
      self.s = s
    def __repr__(self):
      return self.s
      
class Renderable:
    declared = False
    #name_suffix = None
    value_template = "{ %s }"
    def value2js(self,obj):
        raise NotImplementedError
        
    def as_ext(self,request,**kw):
        if self.declared:
            return self.name # as_ext_name()
        else:
            return self.as_ext_value(request,**kw)
        
    def as_ext_value(self,request,**kw):
        options = self.ext_options(request)
        options.update(kw)
        s = self.value_template % ", ".join(["%s: %s" % (k,py2js(v,k)) for k,v in options.items()])
        return mark_safe(s)
        
    #~ def as_ext_name(self):
        #~ return self.name + "_" + self.name_suffix
        
        
class Element(Renderable):
    width = None
    height = None
    def __init__(self,layout,name):
        if layout is not None:
            assert isinstance(layout,Layout)
        self.layout = layout
        self.name = name
        if self.declared:
            layout.variables.append(self)
        
    def __str__(self):
        "This shows how elements are specified"
        if self.width is None:
            return self.name
        if self.height is None:
            return self.name + ":%d" % self.width
        return self.name + ":%dx%d" % (self.width,self.height)
        
    def ext_options(self,request):
        return {}

class Store(Element):
    value_template = "new Ext.data.JsonStore({ %s })"
    declared = True
    
    def __init__(self,layout,report):
        Element.__init__(self,layout,report.name+"_store")
        self.report = report
        
    def ext_options(self,request):
        d = Element.ext_options(self,request)
        d.update(storeId=self.name)
        d.update(remoteSort=True)
        d.update(proxy=js_code(
          "new Ext.data.HttpProxy({url:'%s',method:'GET'})" % \
          self.report.get_absolute_url(json=True)
        ))
        # a JsonStore without explicit proxy sometimes used method POST
        # d.update(url=self.rr.get_absolute_url(json=True))
        # d.update(method='GET')
        d.update(totalProperty='count')
        d.update(root='rows')
        d.update(id=self.report.row_layout.pk.name)
        d.update(fields=js_code(
          "[ %s ]" % ",".join([repr(e.name) 
          for e in self.report.row_layout.ext_store_fields])
        ))
        return d
    
class ColumnModel(Element):
    declared = True
    #name_suffix = "cm"
    value_template = "new Ext.grid.ColumnModel({ %s })"
    
    def __init__(self,layout,report):
        Element.__init__(self,layout,report.name+"_cols")
        self.report = report
        
    #~ def __init__(self,layout,report):
        #~ self.layout = layout # the owning layout
        #~ self.report = report
        #~ self.name = report.name
        
        
    def ext_options(self,request):
        d = Element.ext_options(self,request)
        editing = self.layout.report.can_change.passes(request)
        l = [e.ext_column(editing) for e in self.report.row_layout.leaves()]
        d.update(columns="[ %s ]" % ", ".join(l))
        return d
        
            
        
class HiddenField(Element):
    def __init__(self,layout,field):
        Element.__init__(self,layout,field.attname)
        self.field = field
        
    def value2js(self,obj):
        return getattr(obj,self.name)
        
        
class VisibleElement(Element):
    label = None
    label_width = 0 
    parent = None
    editable = False
    #ext_template = 'lino/includes/element.js'
    def __init__(self,layout,name,width=None,height=None,label=None):
        Element.__init__(self,layout,name)
        self.width = width
        self.height = height
        if label is not None:
            self.label = label
        #    label = name.replace("_"," ")
        #~ if label is not None:
            #~ self.label_width = len(label) + 1
        
    def get_width(self):
        return self.width
        
    def set_width(self,w):
        self.width = w
        
    def leaves(self):
        return [ self ]

    #~ def as_ext(self):
        #~ s = self.ext_editor(label=True)
        #~ if s is not None:
            #~ return mark_safe(s)
        #~ return self.name
        
    
    def ext_options(self,request):
        d = Element.ext_options(self,request)
        if self.width is None:
            """
            an element without explicit width will get flex=1 when in a hbox, otherwise anchor="100%".
            """
            if isinstance(self.parent,HBOX):
                d.update(flex=1)
            else:
                d.update(anchor="100%")
        else:
            d.update(width=(self.width+self.label_width) * EXT_CHAR_WIDTH)
        if self.label:
            d.update(fieldLabel=self.label)
        if self.height is not None:
            d.update(height=(self.height+2) * EXT_CHAR_HEIGHT)
        return d
        
    #~ def as_ext(self):
        #~ try:
            #~ context = dict(
              #~ element = self
            #~ )
            #~ return render_to_string(self.ext_template,context)
        #~ except Exception,e:
            #~ traceback.print_exc(e)
        
    def ext_column(self,editing):
        s = """
        {
          dataIndex: '%s', 
          header: '%s', 
          sortable: true,
        """ % (self.name, self.label)
        if self.width:
            s += " width: %d, " % (self.width * 10)
        if editing and self.editable:
            s += " editor: %s, " % self.ext_editor(label=False)
        s += " } "
        return s
        
        
    def ext_editor(self,label=False):
        s = " new Ext.form.TextField ({ " 
        s += " name: '%s', " % self.name
        if label:
            s += " fieldLabel: '%s', " % self.label
        s += " disabled: true, " 
        s += """
          }) """
        return s
        
    def children(self):
        return [ self ]

class StaticText(VisibleElement):
    def __init__(self,text):
          self.text = mark_safe(text)
    def render(self,row):
        return self.text
          
django2ext = (
    (models.TextField, 'Ext.form.TextArea'),
    (models.CharField, 'Ext.form.TextField'),
    (models.DateField, 'Ext.form.DateField'),
    (models.IntegerField, 'Ext.form.NumberField'),
    (models.DecimalField, 'Ext.form.NumberField'),
    (models.BooleanField, 'Ext.form.Checkbox'),
    (models.ForeignKey, 'Ext.form.ComboBox'),
    (models.AutoField, 'Ext.form.NumberField'),
)


def ext_class(field):
    for cl,x in django2ext:
        if isinstance(field,cl):
            return x
            
_ext_options = (
    (models.TextField, dict(xtype='textarea')),
    (models.CharField, dict(xtype='textfield')),
    (models.DateField, dict(xtype='datefield')),
    (models.IntegerField, dict(xtype='numberfield')),
    (models.DecimalField, dict(xtype='numberfield')),
    (models.BooleanField, dict(xtype='checkbox')),
    (models.ForeignKey, dict(xtype='combo')),
    (models.AutoField, dict(xtype='numberfield')),
)
            
def ext_options(field):
    for cl,x in _ext_options:
        if isinstance(field,cl):
            return x

class ForeignKeyField(FieldElement)
    def __init__(self,layout,field,**kw):
        FieldElement.__init__(self,layout,field,**kw)
        if self.editable:
            self.store = Store(layout,)
    def get_field_options(self,request):
      
class FieldElement(VisibleElement):
    declared = True
    #name_suffix = "field"
    def __init__(self,layout,field,**kw):
        VisibleElement.__init__(self,layout,field.name,
            label=field.verbose_name,**kw)
        self.field = field
        self.editable = field.editable
        
    def value2js(self,obj):
        return getattr(obj,self.name)
        
    def render(self,row):
        return row.render_field(self)
        
    def ext_editor(self,label=False):
        cl = ext_class(self.field)
        if not cl:
            print "no ext editor class for field ", \
              self.field.__class__.__name__, self
            return None
        s = " new %s ({ " % cl
        s += " name: '%s', " % self.name
        if label:
            s += " fieldLabel: '%s', " % self.label
        if not self.field.blank:
            s += " allowBlank: false, "
        if isinstance(self.field,models.CharField):
            s += " maxLength: %d, " % self.field.max_length
        s += """
          }) """
        return s
        
    def as_ext_value(self,request,**kw):
        """
        ExtJS renders fieldLabels only if the field's container has layout 'form', so we create a panel around each field
        """
        panel_options = VisibleElement.ext_options(self,request,**kw)
        panel_options.update(xtype='panel',layout='form')
        field_options = ext_options(self.field)
        field_options.update(name=self.name)
        field_options.update(anchor="100%")
        for o in ('fieldLabel','name'):
            v = panel_options.pop(o,None)
            if v is not None:
                field_options[o] = v
        if not self.field.blank:
            field_options.update(allowBlank=False)
        if isinstance(self.field,models.CharField):
            field_options.update(maxLength=self.field.max_length)
        if isinstance(self.field,models.ForeignKey):
            #print self.field.related_name
            from . import reports
            rpt = reports.get_combo_report(self.field.rel.to)
            r = rpt.renderer(request)
            field_options.update(store=js_code(r.as_ext_store()))
            field_options.update(valueField=rpt.model._meta.pk.attname)
            field_options.update(displayField=rpt.display_field)
            field_options.update(typeAhead=True)
            field_options.update(mode='remote')
            field_options.update(triggerAction='all')
            field_options.update(emptyText='Select a %s...' % rpt.model.__name__)
            field_options.update(selectOnFocus=True)
            field_options.update(hiddenName=self.name+"Hidden")
        field = "{ "
        field += ", ".join(["%s: %s" % (k,py2js(v,k)) for k,v in field_options.items()])
        field += " }"
        s = "{ "
        s += ", ".join(["%s: %s" % (k,py2js(v,k)) for k,v in panel_options.items()])
        s += ", items: [ %s ] " % field
        s += " }"
        return s
            
        
class GridElement(VisibleElement):
    declared = True

    def __init__(self,layout,report,**kw):
        VisibleElement.__init__(self,layout,report.name+"_grid",**kw)
        self.report = report
        self.store = Store(layout,report)
        self.column_model = ColumnModel(layout,report)
      
    def ext_options(self,request):
        #print self.name, self.layout.detail_reports
        #rpt = self.slave
        #r = rpt.renderer(request)
        # print rpt
        d = VisibleElement.ext_options(self,request)
        d.update(xtype='grid')
        d.update(store=self.store)
        d.update(colModel=self.column_model)
        #d.update(store=js_code(self.name+"_store"))
        #d.update(colModel=js_code(self.name+"_cm"))
        #d.update(store=js_code(rpt.as_ext_store()))
        #d.update(colModel=js_code(r.as_ext_colmodel()))
        return d
            
    def value2js(self,obj):
        return "1"

class MethodElement(VisibleElement):

    def __init__(self,layout,name,meth,**kw):
        VisibleElement.__init__(self,layout,name,**kw)
        self.meth = meth
        print "MethodElement", name, meth
        
    def value2js(self,obj):
        fn = getattr(obj,self.name)
        return fn()
        
    def render(self,row):
        return row.render_field(self)

class Container(VisibleElement):
    ext_template = 'lino/includes/element.js'
    ext_container = 'Ext.Panel'
    vertical = False
    hpad = 1
    is_fieldset = False
    
    def __init__(self,layout,name,*elements,**kw):
        VisibleElement.__init__(self,layout,name,**kw)
        #print self.__class__.__name__, elements
        #self.label = kw.get('label',self.label)
        self.elements = []
        for elem in elements:
            assert elem is not None
            if type(elem) == str:
                if "\n" in elem:
                    lines = []
                    for line in elem.splitlines():
                        line = line.strip()
                        if len(line) > 0 and not line.startswith("#"):
                            lines.append(layout,line)
                        self.elements.append(VBOX(layout,None,*lines))
                else:
                    for name in elem.split():
                        if not name.startswith("#"):
                            self.elements.append(layout[name])
            else:
                self.elements.append(elem)
        self.compute_width()
        
        # some more analysis:
        for e in self.elements:
            e.parent = self
            if isinstance(e,FieldElement):
                self.is_fieldset = True
                #~ if self.label_width < e.label_width:
                    #~ self.label_width = e.label_width
                if self.vertical and e.label:
                    w = len(e.label) + 1 
                    if self.label_width < w:
                        self.label_width = w
            if e.width == self.width:
                """
                this was the width-giving element. 
                remove this width to avoid padding differences.
                """
                e.width = None
                
    def compute_width(self):
        """
        If all children have a width (in case of a horizontal layout), 
        or (in a vertical layout) if at at least one element has a width, 
        then my width is also known.
        """
        if self.width is None:
            #print self, "compute_width..."
            w = 0
            if self.vertical:
                #~ if self.name == 'main' and self.layout._model.__name__ == 'Product':
                    #~ print "foo", [e.width for e in self.elements]
                for e in self.elements:
                    if e.width is not None:
                        w = max(e.width,w)
            else:
                for e in self.elements:
                    if e.width is None:
                        return
                    w += e.width
            if w > 0:
                self.width = w
                
        
    def children(self):
        return self.elements
        
    def leaves(self):
        l = []
        for e in self.elements:
            l += e.leaves()
        return l
        
    def __str__(self):
        s = Element.__str__(self)
        # self.__class__.__name__
        s += "(%s)" % (",".join([str(e) for e in self.elements]))
        return s
            
    def render(self,row):
        try:
            context = dict(
              element = BoundElement(self,row),
              renderer = row.renderer
            )
            return render_to_string(self.template,context)
        except Exception,e:
            traceback.print_exc(e)
            raise
            #print e
            #return mark_safe("<PRE>%s</PRE>" % e)

    def ext_options(self,request):
        d = VisibleElement.ext_options(self,request)
        if self.is_fieldset:
            d.update(labelWidth=self.label_width * EXT_CHAR_WIDTH)
        #if not self.is_fieldset:
        d.update(frame=self.layout.frame)
        d.update(labelAlign=self.layout.labelAlign)
        l = [e.as_ext(request) for e in self.elements ]
        d.update(items=js_code("[\n  %s\n]" % (", ".join(l))))
        return d
            
    #~ def as_ext(self,request,**kw):
        #~ options = self.ext_options(request)
        #~ options.update(kw)
        #~ s = "{ "
        #~ s += ", ".join(["%s: %s" % (k,py2js(v,k)) for k,v in options.items()])
        #~ s += ", items: [\n  %s\n]" % (", ".join([e.as_ext(request) for e in self.elements]))
        #~ #s += extra
        #~ s += " }\n"
        #~ return mark_safe(s)
        
        

class HBOX(Container):
    #template = "lino/includes/hbox.html"
    #ext_layout = 'Ext.layout.HBoxLayout'
        
    def ext_options(self,request):
        d = Container.ext_options(self,request)
        d.update(xtype='panel')
        d.update(layout='hbox')
        return d
        
class VBOX(Container):
    #template = "lino/includes/vbox.html"
    vertical = True
    #ext_layout = 'Ext.layout.VBoxLayout'
    
                
    def ext_options(self,request):
        d = Container.ext_options(self,request)
        #~ if self.is_fieldset:
            #~ d.update(xtype='fieldset')
            #~ d.update(layout='form')
        #~ else:
            #~ d.update(xtype='panel')
            #~ d.update(layout='vbox')
        d.update(xtype='panel')
        #d.update(layout='vbox')
        d.update(layout='anchor')
        return d
        
    
class GRID_ROW(Container):
    template = "lino/includes/grid_row.html"
    
class GRID_CELL(Container):
    template = "lino/includes/grid_cell.html"

class TAB(Container):
    vertical = True
    def ext_options(self,request):
        d = Container.ext_options(self,request)
        d.update(xtype='tabpanel')
        d.update(layout='fit')
        #d.update(activeTab=0)
        return d

class Layout(Renderable):
    label = "General"
    #detail_reports = {}
    join_str = None # set by subclasses
    vbox_class = VBOX
    hbox_class = HBOX
    width = None
    
    # ExtJS options
    frame = True
    labelAlign = 'top'
    
    def __init__(self,report,desc=None,main=None):
        #from . import reports
        #assert isinstance(report,reports.Report)
        self.variables = []
        self.slave_grids = []
        self.master_store = Store(self,report)
        self.report = report
        #self._slave_dict = {}
        if main is None:
            if hasattr(self,"main"):
                main = self.create_element('main')
            else:
                if desc is None:
                    desc = self.join_str.join([ 
                        f.name for f in report.model._meta.fields 
                        + report.model._meta.many_to_many])
                main = self.desc2elem("main",desc)
                #~ for e in main.leaves():
                    #~ if e.name == report.model._meta.pk.name

        self._main = main
        
        #~ self.slaves = [ 
          #~ e.slave for e in self.leaves() 
            #~ if isinstance(e,SlaveElement) ]
        
        self.fields = tuple([ 
            e for e in self.leaves() 
                if isinstance(e,FieldElement) ])
              
        pk = None
        for e in self.leaves():
            if e.name == report.model._meta.pk.name:
                pk = e
                break
                
        if pk is None:
            self.pk = self.add_hidden_field(report.model._meta.pk)
            self.ext_store_fields = tuple(self.leaves()+[self.pk])
        else:
            self.pk = pk
            self.ext_store_fields = tuple(self.leaves())
        

    #~ def add_variable(self,e):
        #~ name = e.as_ext_name()
        #~ assert not self.variables.has_key(name)
        #~ self.variables[name] = e
              
    #~ def slaves(self):
        #~ for e in self.leaves():
            #~ if isinstance(e,SlaveElement):
                #~ yield e.slave
        
            
    def desc2elem(self,name,desc,**kw):
        if "\n" in desc:
            lines = []
            i = 0
            for line in desc.splitlines():
                line = line.strip()
                i += 1
                if len(line) > 0 and not line.startswith("#"):
                    lines.append(self.desc2elem(name+'_'+str(i),line,**kw))
            if len(lines) == 1:
                return lines[0]
            return self.vbox_class(self,name,*lines,**kw)
        else:
            l = []
            for x in desc.split():
                if not x.startswith("#"):
                    l.append(self.create_element(x))
            if len(l) == 1:
                return l[0]
            return self.hbox_class(self,name,*l,**kw)
            
    def create_element(self,name):
        #print self.__class__.__name__, "__getitem__()", name
        name,kw = self.splitdesc(name)
        try:
            value = getattr(self,name)
        except AttributeError,e:
            #return self.report.create_element()
            slaveclass = self.report.get_slave(name)
            if slaveclass is not None:
                slaverpt = slaveclass()
                #self._slave_dict[name] = slaverpt
                e = GridElement(self,slaverpt,**kw)
                self.slave_grids.append(e)
                return e
            try:
                field = self.report.model._meta.get_field(name)
            except models.FieldDoesNotExist,e:
                meth = getattr(self.report.model,name,None)
                if meth is not None:
                    return MethodElement(self,name,meth,**kw)
            else:
                return FieldElement(self,field,**kw)
        else:
            if type(value) == str:
                return self.desc2elem(name,value,**kw)
            if isinstance(value,StaticText):
                return value
            #print value
        raise KeyError("%s has no attribute '%s' used in layout %s" % (self.report.model.__name__,name,self.__class__))
        
         
    def splitdesc(self,picture):
        a = picture.split(":",1)
        if len(a) == 1:
            return picture,{}
        if len(a) == 2:
            name = a[0]
            a = a[1].split("x",1)
            if len(a) == 1:
                return name, dict(width=int(a[0]))
            elif len(a) == 2:
                return name, dict(width=int(a[0]),height=int(a[1]))
        raise Exception("Invalid picture descriptor %s" % picture)
                
    def __str__(self):
        s = self.__class__.__name__ 
        if hasattr(self,'_main'):
            s += "(%s)" % self._main
        return s
        
    def add_hidden_field(self,field):
        return HiddenField(self,field)
        
    def bound_to(self,row):
        return BoundElement(self._main,row)

    def get_label(self):
        if self.label is None:
            return self.__class__.__name__
        return self.label
        
    def leaves(self):
        return self._main.leaves()
        
    def ext_options(self,request):
        return self._main.ext_options(request)
        
    #~ def as_ext(self):
        #~ try:
          #~ return self._main.as_ext()
        #~ except Exception,e:
          #~ traceback.print_exc(e)

    def old_get_slave(self,name):
        return self._slave_dict[name]
        
    def renderer(self,report_renderer):
        return LayoutRenderer(self,report_renderer)
        
class RowLayout(Layout):
    show_labels = False
    join_str = " "
    hbox_class = GRID_ROW
    vbox_class = GRID_CELL
    ext_layout = 'Ext.layout.HBoxLayout'
    
    
class PageLayout(Layout):
    show_labels = True
    join_str = "\n"
    ext_layout = ""
    
    def ext_options(self,request):
        d = Layout.ext_options(self,request)
        d.update(bbar = js_code("""new Ext.PagingToolbar({
          store: master_store,       
          displayInfo: true,
          pageSize: 1,
          prependButtons: true,
        }) """))
        return d
        
    def as_ext_value(self,request,**kw):
        options = self.ext_options(request)
        options.update(kw)
        s = "new Ext.form.FormPanel({items: [ %s ]})" % self._main.as_ext_value(request,**options)
        return mark_safe(s)

class TabbedPageLayout(PageLayout):
  
    def __init__(self,report,page_layouts):
        # tabs is a list of PageLayout classes
        tabs = [tc(report) for tc in page_layouts]
        l = [tab._main for tab in tabs]
        main = TAB(self,"tabs",*l)
        PageLayout.__init__(self,report,main=main)
        
class LayoutRenderer:
    def __init__(self,layout,report_renderer):
        self.layout = layout
        self.report = report_renderer
        self.request = report_renderer.request
        self.fields = layout.fields
        #self.slaves = [ rpt.renderer(self.request) for rpt in layout.slave_grids ]
        
    def as_ext_value(self):
      try:
        s = self.layout.as_ext_value(self.request)
        return mark_safe(s)
      except Exception,e:
        traceback.print_exc(e)
        
    def ext_globals(self):
      try:
        #s = "master_store = %s; " % self.report.as_ext_store()
        s = ''
        #~ for slave in self.slaves:
            #~ s += "\n%s_cm = %s;" % (slave.name,slave.as_ext_colmodel())
            #~ s += "\n%s_store = %s;" % (slave.name,slave.as_ext_store())
        for e in self.layout.variables:
            s += "\n%s = %s;" % (e.name,e.as_ext_value(self.request))
        s += "\nfrm = %s;" % self.as_ext_value()
        s += """
%s.addListener('load',function(store,rows,options) { """ % self.layout.master_store.name
        s += """
    frm.form.loadRecord(rows[0]);
    """
        for slave in self.layout.slave_grids:
            s += """
  %s.load({params: { master: rows[0].data['%s'] } });""" % (
      slave.name,self.report.pk.name)
        s += "\n});"
        return mark_safe(s)
      except Exception,e:
        traceback.print_exc(e)
        
    #~ def slaves(self):
      #~ try:
        #~ for sl in self.layout.slaves:
            #~ yield sl.renderer(self.request)
      #~ except Exception,e:
        #~ traceback.print_exc(e)
        
    
class unused_BoundElement:
    def __init__(self,element,row):
        assert isinstance(element,Element)
        self.element = element
        self.row = row
        #from lino.django.utils.render import Row
        #assert isinstance(row,Row)

    def as_html(self):
        try:
            return self.element.render(self.row)
        except Exception,e:
            print "Exception in BoundElement.as_html():"
            traceback.print_exc()
            raise e
  
    #~ def as_json(self):
        #~ return self.element.render_as_json(self.row)
        
    def __unicode__(self):
        return self.as_html()
        
    def children(self):
        try:
            assert isinstance(self.element,Container), "%s is not a Container" % self.element
            for e in self.element.elements:
                yield BoundElement(e,self.row)
        except Exception,e:
            print "Exception in BoundElement.children():"
            traceback.print_exc()
            raise e
            
    def row_management(self):
        return self.row.management()
        
    def unused_row_management(self):
        #print "row_management", self.element
        try:
            assert isinstance(self.element,GRID_ROW)
            #row = self.renderer.get_row()
            #s = "<td>%s</td>" % self.row.links()
            l = []
            if self.row.renderer.has_actions():
                l.append(unicode(
              self.renderer.selector[IS_SELECTED % self.row.number]))

            s = ''
            if self.row.renderer.editing:
                s += "<td>%d%s</td>" % (self.row.number,
                    self.row.pk_field())
                if self.row.renderer.can_delete:
                    s += "<td>%s</td>" % self.row.form["DELETE"]
            else:
                s += "<td>%d</td>" % (self.row.number)
            return mark_safe(s)
        except Exception,e:
            print "Exception in BoundElement.row_management() %s:" % \
                 self.row.renderer.request.path
            traceback.print_exc()
            raise e


