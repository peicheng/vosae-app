# -*- coding:Utf-8 -*-

from django.utils.translation import ugettext as _, pgettext
from django.template.defaultfilters import floatformat
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    Frame,
    PageTemplate,
    NextPageTemplate
)

from core.pdf.report import (
    Report,
    NoSplitFrame,
    BaseTableStyle
)
from core.pdf.utils import Paragraph
from core.pdf.conf import colors
from core.pdf.conf.fonts import get_font
from invoicing import currency_format

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


__all__ = ('InvoiceBaseReport',)


class InvoiceBaseReport(Report):
    """Base class for all InvoiceBase documents reports"""
    
    def __init__(self, report_settings, invoice_base, *args, **kwargs):
        from invoicing.models import InvoiceBase
        if not isinstance(invoice_base, InvoiceBase):
            raise TypeError('InvoiceBaseReport shoud receive an InvoiceBase as invoice_base argument')
        super(InvoiceBaseReport, self).__init__(report_settings, *args, **kwargs)
        self.invoice_base = invoice_base

    def set_metadata(self):
        # Metadata
        if self.invoice_base.issuer:
            self.doc.author = self.invoice_base.issuer.get_full_name()
        if self.invoice_base.reference:
            document_name = ' '.join([
                unicode(self.invoice_base.RECORD_NAME).upper(),
                self.invoice_base.reference
            ])
            self.doc.title = document_name
            self.doc.subject = document_name
        self.doc.creator = self.invoice_base.tenant.name
        self.doc.keywords = self.invoice_base.keywords

    def generate_templates(self):
        frame_kwargs = {
            # 'showBoundary': 1,
            'leftPadding': 0,
            'rightPadding': 0,
            'topPadding': 0,
            'bottomPadding': 0
        }
        address_frame_kwargs = frame_kwargs.copy()
        address_frame_kwargs.update(bottomPadding=2 * mm)

        sender_frame = NoSplitFrame(20 * mm, 260 * mm, 100 * mm, 25 * mm, **frame_kwargs)
        billing_frame = NoSplitFrame(20 * mm, 212 * mm, 75 * mm, 40 * mm, **address_frame_kwargs)
        shipping_frame = NoSplitFrame(115 * mm, 212 * mm, 75 * mm, 40 * mm, **address_frame_kwargs)
        rest_frame = Frame(20 * mm, 25 * mm, 170 * mm, 160 * mm, **frame_kwargs)
        full_frame = Frame(20 * mm, 25 * mm, 170 * mm, 247 * mm, **frame_kwargs)

        self.doc.addPageTemplates([
            PageTemplate(id='First', frames=[sender_frame, billing_frame, shipping_frame, rest_frame], onPage=self.on_first_page_cb),
            PageTemplate(id='Other', frames=[full_frame], onPage=self.on_other_pages_cb),
        ])
        self.story.append(NextPageTemplate('Other'))

    def generate_style(self):
        super(InvoiceBaseReport, self).generate_style()
        self.style.add(ParagraphStyle(
            name='Address',
            parent=self.style['Normal'],
            fontName=get_font(self.settings.font_name).bold,
            fontSize=1.2 * self.settings.font_size,
            leading=1.45 * self.settings.font_size
        ))

        self.style.add(BaseTableStyle(
            name='InvoiceBaseReferencesTable',
            parent=self.style['ReportTable'],
            cmds=[
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
                ('FONTSIZE', (0, 0), (0, 0), 1.5 * self.settings.font_size),
                ('FONTSIZE', (-1, 0), (-1, 0), 1.2 * self.settings.font_size),
                ('LEADING', (0, 0), (0, 0), 2 * self.settings.font_size),
                ('LEADING', (-1, 0), (-1, 0), 1.5 * self.settings.font_size),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]
        ))

        self.style.add(BaseTableStyle(
            name='InvoiceBaseItemsTable',
            parent=self.style['ReportTable'],
            cmds=[
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.settings.hex_font_base_color),
                ('BACKGROUND', (0, 0), (-1, 0), self.settings.hex_base_color),
            ]
        ))

        self.style.add(BaseTableStyle(
            name='InvoiceBaseSummaryTable',
            parent=self.style['Table'],
            cmds=[
                ('FONTNAME', (0, -1), (-1, -1), get_font(self.settings.font_name).bold),
                ('FONTSIZE', (0, -1), (-1, -1), 1.2 * self.settings.font_size),
                ('LEADING', (0, -1), (-1, -1), 1.5 * self.settings.font_size),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (-2, -1), (-1, -1), self.settings.hex_font_base_color),
                ('BACKGROUND', (-1, 0), (-1, -1), self.settings.hex_base_color.clone(alpha=0.1)),
                ('BACKGROUND', (-2, -1), (-1, -1), self.settings.hex_base_color),
                ('LINEBELOW', (0, 0), (-1, -2), 4, colors.white),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -2), 6),
            ]
        ))

    def on_first_page_cb(self, canvas, document):
        super(InvoiceBaseReport, self).on_first_page_cb(canvas, document)
        self.draw_main_line(canvas, document)
        self.draw_addresses_labels(canvas, document)

    def draw_main_line(self, canvas, document):
        # Main line
        canvas.saveState()
        canvas.setLineWidth(1.5 * mm)
        canvas.setLineCap(1)
        canvas.setStrokeColor(colors.darkgrey)
        canvas.line(20 * mm, 193 * mm, 190 * mm, 193 * mm)
        canvas.restoreState()

    def draw_addresses_labels(self, canvas, document):
        # Addresses labels
        canvas.saveState()
        canvas.setLineWidth(0.2)
        canvas.setLineCap(1)
        canvas.setStrokeColor(self.settings.hex_base_color)
        canvas.setFont(get_font(self.settings.font_name).regular, 9)
        canvas.setFillColor(self.settings.hex_base_color)
        canvas.line(20 * mm, 212 * mm, 95 * mm, 212 * mm)
        canvas.line(115 * mm, 212 * mm, 190 * mm, 212 * mm)
        canvas.drawString(20 * mm, 208 * mm, _("Billing address").upper())
        canvas.drawString(115 * mm, 208 * mm, _("Delivery address").upper())
        canvas.restoreState()

    def footer(self, canvas, document):
        super(InvoiceBaseReport, self).footer(canvas, document)

        # Registration information
        registration_info_text = u' - '.join([self.invoice_base.tenant.name] + self.invoice_base.tenant.registration_info.get_list())

        canvas.saveState()
        registration_info = Paragraph(registration_info_text, style=self.style['Smaller'])
        available_width, available_height = (140 * mm, 16 * mm)
        w, h = registration_info.wrap(available_width, available_height)
        registration_info.drawOn(canvas, document.leftMargin, available_height - h)
        canvas.restoreState()

    def fill(self):
        """Fills the report"""
        # Sender part
        self.fill_sender()

        # Billing address
        self.next_frame()
        self.fill_billing_address()
        
        # Delivery address
        self.next_frame()
        self.fill_delivery_address()

        # Description
        self.next_frame()
        self.fill_description()

        # Line items
        self.fill_line_items()

        # Line items summary
        self.fill_line_items_summary()

        # Legal notice
        self.fill_legal_notice()


    def fill_sender(self):
        """Fills sender identity"""
        from reportlab.platypus.flowables import Image
        from core.pdf.utils import Paragraph
        # Sender identity
        sender_paragraphs = []
        if self.invoice_base.current_revision.sender:
            sender_paragraphs.append(Paragraph(self.invoice_base.current_revision.sender, self.style['Small']))
        sender_paragraphs.append(Paragraph(self.invoice_base.tenant.name, self.style['Small']))
        if self.invoice_base.current_revision.sender_address:
            sender_paragraphs.append(Paragraph(u'\n'.join(self.invoice_base.current_revision.sender_address.get_formatted()), self.style['Small']))
        # Add layout table if logo or paragraphs
        if self.invoice_base.tenant.logo_cache:
            logo = Image(self.invoice_base.tenant.logo_cache)
            logo_width, logo_height = logo._restrictSize(50 * mm, 20 * mm)
            self.table(
                [[logo, sender_paragraphs]],
                (logo_width + 4 * mm, None),
                self.style['LayoutTable'],
                rowHeights=(20 * mm,)
            )
        else:
            for paragraph in sender_paragraphs:
                self.append(paragraph)

    def fill_billing_address(self):
        """Fills billing address"""
        # Billing address frame
        if self.invoice_base.current_revision.contact:
            self.p(self.invoice_base.current_revision.contact.get_full_name(upper_name=True), style=self.style['Address'])
        if self.invoice_base.current_revision.organization:
            self.p(self.invoice_base.current_revision.organization.corporate_name, style=self.style['Address'])
        if self.invoice_base.current_revision.billing_address:
            self.p(u'\n'.join(self.invoice_base.current_revision.billing_address.get_formatted()), style=self.style['Address'])

    def fill_delivery_address(self):
        """Fills delivery address"""
        # Delivery address frame
        if self.invoice_base.current_revision.contact:
            self.p(self.invoice_base.current_revision.contact.get_full_name(upper_name=True), style=self.style['Address'])
        if self.invoice_base.current_revision.organization:
            self.p(self.invoice_base.current_revision.organization.corporate_name, style=self.style['Address'])
        if self.invoice_base.current_revision.delivery_address:
            self.p(u'\n'.join(self.invoice_base.current_revision.delivery_address.get_formatted()), style=self.style['Address'])

    def fill_description(self):
        """Fills the description"""
        pass

    def fill_line_items(self):
        """
        Fills line items table  
        Should start with a spacer
        """
        self.spacer()
        rows = [[
            pgettext('table-headers', 'Description'),
            pgettext('table-headers', 'Qty'),
            pgettext('table-headers', 'Unit price (excl. tax)'),
            pgettext('table-headers', 'Tax'),
            pgettext('table-headers', 'Total (excl. tax)')
        ]]
        for item in self.invoice_base.current_revision.line_items:
            rows.append([
                item.description,
                floatformat(item.quantity, -2),
                currency_format(item.unit_price),
                '{0:.2%}'.format(item.tax.rate),
                currency_format(item.total_price, self.invoice_base.current_revision.currency.symbol)
            ])
        col_widths = (85 * mm, 20 * mm, 20 * mm, 20 * mm, 25 * mm)
        self.table(rows, col_widths, repeatRows=1, style=self.style['InvoiceBaseItemsTable'])

    def fill_line_items_summary(self):  
        """
        Fills line items summary table  
        Should start with a spacer
        """
        self.spacer()
        rows = [[
            _('TOTAL (excl. tax)'),
            currency_format(self.invoice_base.sub_total, self.invoice_base.current_revision.currency.symbol)
        ]]
        for tax in self.invoice_base.taxes_amounts:
            rows.append([
                '%(tax_name)s (%(tax_rate)s)' % {
                    'tax_name': tax.get('name'),
                    'tax_rate': '{0:.2%}'.format(tax.get('rate'))
                },
                currency_format(tax.get('amount'), self.invoice_base.current_revision.currency.symbol)
            ])
        rows.append([
            _('TOTAL (incl. tax)'),
            currency_format(self.invoice_base.amount, self.invoice_base.current_revision.currency.symbol)
        ])
        col_widths = (None, 25 * mm)
        self.start_keeptogether()
        self.table(rows, col_widths, hAlign='RIGHT', style=self.style['InvoiceBaseSummaryTable'])
        self.end_keeptogether()


    def fill_legal_notice(self):
        """
        Fills the legal notice part  
        Should start with a spacer
        """
        pass

    def fill_registration_information(self):
        """Fills the registration information part"""
        registration_info_parts = [self.invoice_base.tenant.name] + self.invoice_base.tenant.registration_info.get_list()
        self.p(u' - '.join(registration_info_parts), style=self.style['Smaller'])
