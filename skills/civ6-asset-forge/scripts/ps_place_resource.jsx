// ps_place_resource.jsx — 资源图标 PS 自动化引擎（首选流程）
// 打开模板 PSD → 只留指定类别底盘可见 → 把已构图图案层贴入 Pattern 组 →
// 原位导出 256×256 RGBA PNG。
// 构图（等比缩放 + 预乘 LANCZOS + 居中）由 ps_place_resource.py 用
// build_resource_icon.place_pattern 预先完成；本脚本不做任何缩放或平移。
// 参数文件约定：%TEMP%/civ6_resource_ps_params.txt（UTF-8，key=value：
// psd / material / outdir / plate / tag），由 ps_place_resource.py 写入。

function readParams(path) {
    var f = new File(path);
    f.encoding = 'UTF-8';
    f.open('r');
    var params = {};
    while (!f.eof) {
        var line = f.readln();
        var i = line.indexOf('=');
        if (i > 0) params[line.substring(0, i)] = line.substring(i + 1);
    }
    f.close();
    return params;
}

function selectLayerByName(name) {
    var desc = new ActionDescriptor();
    var ref = new ActionReference();
    ref.putName(charIDToTypeID('Lyr '), name);
    desc.putReference(charIDToTypeID('null'), ref);
    executeAction(charIDToTypeID('slct'), desc, DialogModes.NO);
}

function placeFile(file) {
    var desc = new ActionDescriptor();
    desc.putPath(charIDToTypeID('null'), new File(file));
    desc.putEnumerated(charIDToTypeID('FTcs'), charIDToTypeID('QCSt'), charIDToTypeID('Qcsa'));
    var offsetDesc = new ActionDescriptor();
    offsetDesc.putUnitDouble(charIDToTypeID('Hrzn'), charIDToTypeID('#Pxl'), 0);
    offsetDesc.putUnitDouble(charIDToTypeID('Vrtc'), charIDToTypeID('#Pxl'), 0);
    desc.putObject(charIDToTypeID('Ofst'), charIDToTypeID('Ofst'), offsetDesc);
    executeAction(charIDToTypeID('Plc '), desc, DialogModes.NO);
}

function main() {
    var params = readParams(Folder.temp.fsName + '/civ6_resource_ps_params.txt');
    app.displayDialogs = DialogModes.NO;

    var doc = app.open(new File(params.psd));

    // Choose Plate：只留指定类别底盘可见
    var choose = null;
    for (var i = 0; i < doc.layerSets.length; i++) {
        if (doc.layerSets[i].name === 'Choose Plate') choose = doc.layerSets[i];
    }
    if (!choose) throw new Error('模板缺少 Choose Plate 组');
    var found = false;
    for (var j = 0; j < choose.artLayers.length; j++) {
        var l = choose.artLayers[j];
        l.visible = (l.name === params.plate);
        if (l.visible) found = true;
    }
    if (!found) throw new Error('模板缺少底盘层 ' + params.plate);

    // Pattern 组：贴入已构图图案层，置顶
    var pattern = null;
    for (var k = 0; k < doc.layerSets.length; k++) {
        if (doc.layerSets[k].name === 'Pattern') pattern = doc.layerSets[k];
    }
    if (!pattern) throw new Error('模板缺少 Pattern 组');
    selectLayerByName('Pattern');
    placeFile(params.material);
    app.activeDocument.activeLayer.name = 'Pattern';

    var outFile = new File(params.outdir + '/' + params.tag + '.png');
    var opts = new PNGSaveOptions();
    doc.saveAs(outFile, opts, true, Extension.LOWERCASE);
    doc.close(SaveOptions.DONOTSAVECHANGES);
    return 'OK ' + params.tag;
}

main();
