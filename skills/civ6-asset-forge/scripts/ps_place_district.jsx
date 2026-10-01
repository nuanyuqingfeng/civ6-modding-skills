// ps_place_district.jsx — 区域图标 PS 自动化引擎（效果最好的首选流程）
// 仿照 PSD 模板人工流程：打开主 PSD → 编辑 District Alpha 智能对象 →
// 隐藏旧素材 → 置入新素材（智能对象非破坏变换，等比适配 256 画布居中）→
// 保存工作稿写回主文档 → 逐区域开关可见性导出 256×256 PNG。
// 参数文件约定：%TEMP%/civ6_district_ps_params.txt（UTF-8，key=value：psd / material / outdir），
// 由 ps_place_district.py 写入。

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

function hideAllLayers(container) {
    for (var i = 0; i < container.layers.length; i++) {
        var l = container.layers[i];
        if (l.typename === 'LayerSet') {
            hideAllLayers(l);
        } else {
            l.visible = false;
        }
    }
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

function fitLayerToDoc(doc, layer) {
    var b = layer.bounds;
    var w = b[2].as('px') - b[0].as('px');
    var h = b[3].as('px') - b[1].as('px');
    var docW = doc.width.as('px');
    var docH = doc.height.as('px');
    var scale = Math.min(docW / w, docH / h) * 100;
    layer.resize(scale, scale, AnchorPosition.MIDDLECENTER);
    b = layer.bounds;
    var cx = (b[0].as('px') + b[2].as('px')) / 2;
    var cy = (b[1].as('px') + b[3].as('px')) / 2;
    layer.translate(docW / 2 - cx, docH / 2 - cy);
}

function selectLayerByName(name) {
    var desc = new ActionDescriptor();
    var ref = new ActionReference();
    ref.putName(charIDToTypeID('Lyr '), name);
    desc.putReference(charIDToTypeID('null'), ref);
    executeAction(charIDToTypeID('slct'), desc, DialogModes.NO);
}

function main() {
    var params = readParams(Folder.temp.fsName + '/civ6_district_ps_params.txt');
    app.displayDialogs = DialogModes.NO;
    app.preferences.interpolation = ResampleMethod.BICUBICAUTOMATIC;

    var doc = app.open(new File(params.psd));

    // 顶层组：只留 Choose District 显示（Import Alpha 等全部隐藏）
    var choose = null;
    for (var i = 0; i < doc.layerSets.length; i++) {
        var ls = doc.layerSets[i];
        if (ls.name === 'Choose District') {
            choose = ls;
            ls.visible = true;
        } else {
            ls.visible = false;
        }
    }

    // 选中第一个区域组（保证智能对象层所在分支可见）并选中 District Alpha
    choose.layerSets[0].visible = true;
    selectLayerByName('District Alpha');

    // 编辑 District Alpha 智能对象 → 打开内嵌工作稿
    executeAction(stringIDToTypeID('placedLayerEditContents'), undefined, DialogModes.NO);
    var inner = app.activeDocument;

    // 隐藏全部旧素材层，置入新素材（智能对象，非破坏变换）
    hideAllLayers(inner);
    placeFile(params.material);
    fitLayerToDoc(inner, inner.activeLayer);

    // 保存工作稿 = 写回主文档智能对象
    inner.close(SaveOptions.SAVECHANGES);

    // 逐区域导出
    var outDir = new Folder(params.outdir);
    if (!outDir.exists) outDir.create();
    var opts = new PNGSaveOptions();
    for (var j = 0; j < choose.layerSets.length; j++) {
        var reg = choose.layerSets[j];
        for (var k = 0; k < choose.layerSets.length; k++) {
            choose.layerSets[k].visible = (k === j);
        }
        doc.saveAs(new File(params.outdir + '/' + reg.name + '.png'), opts, true, Extension.LOWERCASE);
    }

    var count = choose.layerSets.length;
    doc.close(SaveOptions.DONOTSAVECHANGES);
    return 'OK ' + count + ' regions';
}

main();
