// noinspection JSPotentiallyInvalidConstructorUsage

import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

export const exportPNG = async (chartRef, filename) => {
    const canvas = await html2canvas(chartRef.current, { scale: 2 });
    canvas.toBlob((blob) => saveAs(blob, filename));
};

export const exportExcel = (chartData, filename) => {
    const ws = XLSX.utils.json_to_sheet(chartData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Forecast");
    XLSX.writeFile(wb, filename);
};

export const exportPDF = async (chartRef, filename) => {
    const canvas = await html2canvas(chartRef.current, { scale: 2 });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('l', 'mm', 'a4');
    const imgWidth = 280;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
    pdf.save(filename);
};