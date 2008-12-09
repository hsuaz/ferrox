(function($)
{

/**
 * Creates span element with specified text and returns its jQuery object.
 * @returns jQuery object of new span.
 */
var createText = function(text)
{
	return $(['<span>', text, '</span>'].join(''));
};

/**
 * Creates input:text element with specified initial value and size and returns its jQuery object.
 * @returns jQuery object of new input:text.
 */
var createTextField = function(initialValue, size)
{
	return $(['<input disabled="disabled" type="text" value="', initialValue, '" size="', size, '" />'].join(''));
};

/**
 * Creates complex element that acts as pager link and returns its jQuery object.
 * @returns jQuery object of new pager link.
 */
var createPagerLink = function(name, isText)
{
	var pagerLink = $(isText 
		?
		[
		'<div class="page-text-link"><button disabled="disabled" class="', name, '-disabled">', $.fn.grid_widget.locale.pager[name],
		'</button></div>',
		''].join('')
		:
		[
		'<div class="page-link"><button disabled="disabled" class="', name, '-disabled" title="', $.fn.grid_widget.locale.pager[name], '">',
		'&nbsp;',
		'</button></div>',
		''].join('')
		);
	pagerLink.data('name', name).data('disabled', true);
	pagerLink.mouseover(function() { var $this = $(this); if (!$this.data('disabled')) $this.addClass(isText ? 'hot-page-text-link' : 'hot-page-link'); });
	pagerLink.mouseout(function() { $(this).removeClass('hot-page-text-link').removeClass('hot-page-link'); });
	return pagerLink;
};

/**
 * Enables pager link that provided as this argument.
 */
var enablePagerLink = function()
{
	var className = this.data('disabled', false).data('name');
	$('button', this).removeAttr('disabled').removeClass(className + '-disabled').addClass(className);
};

/**
 * Disables pager link that provided as this argument.
 */
var disablePagerLink = function()
{
	var className = this.data('disabled', true).data('name');
	this.removeClass('hot-page-link');
	$('button', this).attr('disabled', 'disabled').addClass(className + '-disabled').removeClass(className);
};
    
/**
 * Sets pager link enablity of given pagerLink to given new value.
 */
var setPagerLink = function(pagerLink, enable)
{
	if (enable)
	{
		enablePagerLink.call(pagerLink);
	}
	else
	{
		disablePagerLink.call(pagerLink);
	}
};

/**
 * Builds new grid control inside this HTML element, as specified by arguments.
 * Note that all inner content will be interpreted as additional arguments and replaced with rendered grid.
 */
var createGrid = function(commonArgs)
{
	var me = $(this);
	var args = {};
	args = $.extend(args, $.fn.grid_widget.defaults, commonArgs);
	var concreteData = $.trim(me.text());
	me.empty();

	var tableDiv = $('<div class="data-grid-view" style="position: relative;"></div>').appendTo(me);
	var viewDiv = $('<div style="position: absolute; left: 0; top: 0; width: 100%; overflow: auto; display: none;"></div>').appendTo(tableDiv);
	var pagerDiv = $('<div class="data-grid-pager"></div>').appendTo(me);
	var toolsDiv = $('<div class="data-grid-tools" style="display: none;"></div>').appendTo(me);
	var pageFirst = createPagerLink('page-first').appendTo(pagerDiv);
	var pagePrev = createPagerLink('page-prev').appendTo(pagerDiv);
	var pageNumberLabel = createText($.fn.grid_widget.locale.pager.pageNumber).appendTo(pagerDiv);
	var pageNumber = createTextField(1, 3).css('text-align', 'right').appendTo(pagerDiv);
	createText($.fn.grid_widget.locale.pager.pageTotal).appendTo(pagerDiv);
	var pageTotal = createText('?').appendTo(pagerDiv);
	var pageNext = createPagerLink('page-next').appendTo(pagerDiv);
	var pageLast = createPagerLink('page-last').appendTo(pagerDiv);
	createText($.fn.grid_widget.locale.pager.separator).appendTo(pagerDiv);
	var refresher = createPagerLink('data-grid-refresh').appendTo(pagerDiv);
	createText($.fn.grid_widget.locale.pager.separator).appendTo(pagerDiv);
	createText($.fn.grid_widget.locale.pager.rowsDisplayed).appendTo(pagerDiv);
	var rowsDisplayed = createText('?').appendTo(pagerDiv);
	createText($.fn.grid_widget.locale.pager.rowsTotal).appendTo(pagerDiv);
	var rowsTotal = createText('?').appendTo(pagerDiv);

	var closeButton = createPagerLink('close-tool', true).appendTo(toolsDiv);
	var csvExport = createPagerLink('csv-export', true).hide().appendTo(pagerDiv);

	var url;
	var start;
	var limit;
	var sortField;
	var sortDirection;
	var total;
	var columns;
	var params;

	var showTotals = function()
	{
		return (('showTotals' in args) && args.showTotals);
	};

	var renderDummy = function()
	{
		var html = ['<table><tr><th>&nbsp;</th></tr>'];
		for (var i = 0; i < limit; i++)
		{
			html.push('<tr><td>&nbsp;</td></tr>');
		}
		if (showTotals())
		{
			html.push('<tr class="totals"><th>&nbsp;</th></tr>');
		}

		html.push('</table>');

		viewDiv.appendTo(toolsDiv);
		tableDiv.html(html.join('')).append(viewDiv);
	};

	var initializeState = function(newArgs)
	{
		args = $.extend(args, newArgs);
		url = args.url;
		start = args.start;
		limit = args.limit;
		sortField =  args['sort'];
		sortDirection = args.dir;
		params = args.params;
		total = 0;
		columns = [];
		if (('csv' in args) && args.csv)
		{
			csvExport.css('display', 'inline');
		}
		else
		{
			csvExport.hide();
		}
		renderDummy();
	};

	var concreteArgs = {};
	if (concreteData != '')
	{
		if (concreteData.charAt(0) == '{') // json
		{
			concreteArgs = eval('(' + concreteData + ')');
		}
		else // url
		{
			concreteArgs.url = concreteData;
		}
	}

	initializeState(concreteArgs);


	var refresh = function()
	{
		delete params.hasTotals;
		delete params.total;
		load();
	};

	// event handlers

	refresher.click(function()
	{
		refresh();
	});

	pageNumberLabel.click(function()
	{
		pageNumber.select().focus();
	});

	pageFirst.click(function()
	{
		start = 0;
		load();
	});

	pagePrev.click(function()
	{
		start -= limit;
		if (start < 0) 
		{
			start = 0;
		}
		load();
	});

	pageLast.click(function()
	{
		var newstart = parseInt((total + limit - 1) / limit) * limit;
		if (newstart >= total)
		{
			newstart -= limit;
		}
		if (start == newstart)
		{
			return;
		}
		start = newstart;
		load();
	});

	pageNext.click(function()
	{
		start += limit;
		if (start >= total) 
		{
			start -= limit;
			return;
		}
		load();
	});

	pageNumber.focus(function()
	{
		this.select();
	});

	pageNumber.keyup(function(e)
	{
		var curPage = parseInt(start / limit) + 1;
		if (e.keyCode == 27)
		{
			pageNumber.val(curPage).select();
		}
	});

	pageNumber.keypress(function(e)
	{
		var curPage = parseInt(start / limit) + 1;
		var pageCount = parseInt((total + limit - 1) / limit);
		if (e.which == 13)
		{
			var newPageNumber = parseInt(pageNumber.val());
			if (isNaN(newPageNumber) || newPageNumber < 1)
			{
				pageNumber.val(curPage).select();
				return;
			}
			if (newPageNumber > pageCount)
			{
				newPageNumber = pageCount;
			}
			start = (newPageNumber - 1) * limit;
			load();
			pageNumber.select();
		}
		
	});

	closeButton.click(function()
	{
		viewDiv.empty().hide();
		pagerDiv.show();
		toolsDiv.hide();
		updateControls();
	});

	// rendering

	var getCellStyle = function(columnIndex)
	{
		var col = columns[columnIndex];
		return [
			(col.hidden ? 'display: none;' : ''),
			'text-align: ', (col.textAlign || 'left'), ';',
			'vertical-align: ', (col.verticalAlign || 'top'), ';',
			(col.style || ''),
			''].join('');
	};

	var updateSortArrows = function()
	{
		var headerCells = $('th', $('tr', tableDiv).eq(0));
		headerCells.removeClass('asc').removeClass('desc');
		if (sortField == '') 
		{
			return;
		}
		var columnIndex = -1;
		for (var i = 0; i < columns.length; i++)
		{
			if (columns[i].name == sortField)
			{
				columnIndex = i;
				break;
			}
		}
		headerCells.eq(columnIndex).addClass((sortDirection == 'ASC') ? 'asc' : 'desc');
	};

	var getSortMethod = function(columnIndex)
	{
		var sortMethod = function()
		{
			if (sortField != columns[columnIndex].name)
			{
				sortField = columns[columnIndex].name;
				sortDirection = 'ASC';
			}
			else
			{
				sortDirection = (sortDirection == 'ASC') ? 'DESC' : 'ASC';
			}
			load();
		};
		return sortMethod;
	};

	var renderRow = function(index)
	{
		var row = $('<tr class="data-empty-row"></tr>');
		for (var i = 0; i < columns.length; i++)
		{
			var cell = $([
				'<td class="', , '" style="', getCellStyle(i), '">&nbsp;</td>',
				''].join(''));
			row.append(cell);
		}

		var getRowData = function()
		{
			var rowData = [];
			$('td', row).each(function() { rowData.push($(this).text()); });
			return rowData;
		};

		row.mouseover(function() { $(this).not('.data-empty-row').addClass('hilite'); });
		row.mouseout(function() { $(this).removeClass('hilite'); });
		row.dblclick(function() {
			if ($(this).hasClass('data-empty-row')) return;
			me.trigger('rowdblclick', [{ index: index, rowEl: row, row: getRowData(), columns: columns }]);
			});
		return row;
	};

	var renderTable = function()
	{
		var table = $('<table></table>');
		var headerRow = $('<tr></tr>');

		for (var i = 0; i < columns.length; i++)
		{
			var col = columns[i];
			var headerCell = $([
				'<th style="', getCellStyle(i), '">', col.title, '</th>',
				''].join(''));
			headerCell.click(getSortMethod(i));
			headerRow.append(headerCell);
		}
		table.append(headerRow);

		for (var i = 0; i < limit; i++)
		{
			var row = renderRow(i);
			table.append(row);
		}

		if (showTotals())
		{
			var totalsRow = $('<tr class="totals"></tr>');

			for (var i = 0; i < columns.length; i++)
			{
				var col = columns[i];
				var totalsCell = $([
				'<th style="', getCellStyle(i), '">&nbsp;</th>',
				''].join(''));
				totalsRow.append(totalsCell);
			}
			table.append(totalsRow);
		}

		viewDiv.appendTo(toolsDiv);
		tableDiv.empty().append(table).append(viewDiv);
	};

	var fillTable = function(data)
	{
		for (var i = 0; i < data.length; i++)
		{
			var row = $('tr', tableDiv).eq(i + 1).removeClass('data-empty-row');
			var cells = $('td', row);
			for (var j = 0; j < columns.length; j++)
			{
				var rd = columns[j].renderer(data[i][j], { rowData: data[i], columns: columns, columnIndex: j, mode: 'dataRow'});
				cells.eq(j).empty().append(rd);
			}
		}
		for (var i = data.length; i < limit; i++)
		{
			var row = $('tr', tableDiv).eq(i + 1).addClass('data-empty-row');
			var cells = $('td', row);
			for (var j = 0; j < columns.length; j++)
			{
				cells.eq(j).html('&nbsp;');
			}
		}
	};

	var fillTotals = function(totals)
	{
		var cells = $('tr.totals>th', tableDiv);
		if (cells.length == 0) return;
		if (totals == null) totals = [];
		for (var i = 0; i < totals.length; i++)
		{
			var rtd = columns[i].renderer(totals[i], { rowData: totals, columns: columns, columnIndex: i, mode: 'totals'});
			cells.eq(i).empty().append(rtd);
		}
		params.hasTotals = 1;
	};

	var updateControls = function()
	{
		var curPage = parseInt(start / limit) + 1;
		var pageCount = parseInt((total + limit - 1) / limit);
		var rowsPerPage = limit;
		if (start + rowsPerPage > total)
		{
			rowsPerPage = total - start;
		}
		pageTotal.html(pageCount);
		rowsTotal.html(total);
		if (total > 0)
		{
			pageNumber.val(curPage).removeAttr('disabled');
			rowsDisplayed.html([start + 1, start + rowsPerPage].join('&nbsp; - &nbsp;'));
		}
		else
		{
			pageNumber.val('').attr('disabled', 'disabled');
			rowsDisplayed.html('?');
		}
		setPagerLink(refresher, true);
		setPagerLink(pageFirst, curPage != 0 && curPage > 1);
		setPagerLink(pagePrev, curPage != 0 && curPage > 1);
		setPagerLink(pageNext, curPage != 0 && curPage < pageCount);
		setPagerLink(pageLast, curPage != 0 && curPage < pageCount);
		setPagerLink(csvExport, true);
		setPagerLink(closeButton, true);
	};

	var render = function(data)
	{
		if ('total' in data)
		{
			total = parseInt(data.total);
			params.total = total;
		}
		closeButton.click();
		fillTable(data.data);
		if (showTotals())
		{
			fillTotals(data.totals);
		}
		updateControls();
		updateSortArrows();
	};

	var disableControls = function()
	{
		pageNumber.attr('disabled', 'disabled');
		setPagerLink(refresher, false);
		setPagerLink(pageFirst, false);
		setPagerLink(pagePrev, false);
		setPagerLink(pageNext, false);
		setPagerLink(pageLast, false);
		setPagerLink(csvExport, false);
	};

	// data loading

	var getUrlParams = function(mode)
	{
		var r = $.extend({}, params, {
			start: start,
			limit: limit,
			"sort": sortField,
			dir: sortDirection
			});
		switch (mode)
		{
		case 'csv':
			r.csv = 1;
			break;
		}
		return r;
	};
	
	var renderCsv = function(data)
	{
		toolsDiv.show();
		pagerDiv.hide();
		var d = $('<textarea style="width: 100%; overflow: auto;"></textarea>');
		var csv = [];
		
		data = data.data;

		for (var i = 0; i < columns.length; i++)
		{
			if (i > 0) csv.push(';');
			var col = columns[i];
			csv.push(col.title);
		}
		csv.push("\r\n");
		for (var i = 0; i < data.length; i++)
		{
			for (var j = 0; j < columns.length; j++)
			{
				if (j > 0) csv.push(';');
				csv.push(data[i][j]);
			}
			csv.push("\r\n");
		}
		d.val(csv.join(''));
		viewDiv.html(d).show().focus().select();
	};

	var loadCSV = function()
	{
		disableControls();
		$.getJSON(url, getUrlParams('csv'), renderCsv);
	};

	var load = function()
	{
		disableControls();
		$.getJSON(url, getUrlParams(), render);
	};

	var columnsLoaded = function(json)
	{
		var isSortFieldOk = (sortField == '');
		columns = json.metadata;
		for (var i = 0; i < columns.length; i++)
		{
			var col = columns[i];
			var rendererName = col.renderer || 'default';
			col.renderer = $.fn.grid_widget.renderers[rendererName] || $.fn.grid_widget.renderers['default'];
			if (col.name == sortField)
			{
				isSortFieldOk = true;
			}
		}
		if (!isSortFieldOk)
		{
			sortField = '';
		}
		renderTable();
		if ('data' in json)
		{
			render(json);
		}
		else
		{
			load();
		}
	};

	var configure = function()
	{
		disableControls();
		delete params.hasTotals;
		delete params.total;
		$.getJSON(url, $.extend({ columns: 1 }, getUrlParams()), columnsLoaded);
	};

	csvExport.click(loadCSV);

	this.grid_widgetConfigure = function(args)
	{
		initializeState(args);
		configure();
	};

	this.grid_widgetRefresh = function()
	{
		refresh();
	};

	configure();
};

/**
 * Builds new grid controls for each elment specified by this jQuery object, as specified by arguments.
 * Note that all inner content will be interpreted as additional arguments and replaced with rendered grids.
 * This is jQuery plugin.
 * @addon
 */
$.fn.grid_widget = function(args)
{
	if (!args) args = {};
	$(this).each(function() { createGrid.call(this, args); });

	return this;
};

$.fn.grid_widgetConfigure = function(args)
{
	if (!args) args = {};
	$(this).each(function() { this.grid_widgetConfigure(args); });

	return this;
};

$.fn.grid_widgetRefresh = function()
{
	$(this).each(function() { this.grid_widgetRefresh(); });
	return this;
};


$.fn.grid_widget.defaults = {
	start: 0,
	limit: 50,
	'sort': '',
	dir: 'ASC',
	params: {}
	};

$.fn.grid_widget.locale = {
	pager: {
		'page-first': 'First page',
		'page-last': 'Last page',
		'page-prev': 'Previous page',
		'page-next': 'Next page',
		pageNumber: 'Page&nbsp;',
		pageTotal: '&nbsp;of&nbsp;',
		rowsDisplayed: '&nbsp;&nbsp;Displaying records&nbsp;',
		rowsTotal: '&nbsp;of&nbsp;',
		refresh: 'Refresh',
		'csv-export': 'Export to CSV',
		'close-tool': 'Close',
		separator: '&nbsp;|&nbsp;'
		}
	};

var defaultRenderer = function(x)
{
	if (!x) return '&nbsp;';
	return x.toString()
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		;
};

var htmlRenderer = function(x)
{
	return x ? x.toString() : '&nbsp;';
};

$.fn.grid_widget.renderers = {
	'default': defaultRenderer,
	'html': htmlRenderer
	};


// automated filter form handling

$.fn.grid_widgetForm = function(args)
{
	var params = args.params || {};
	var grid = args.grid;
	if (typeof(grid) == 'string')
	{
		grid = $(grid);
	}

	var getFormParams = function(f)
	{
		var p = $.extend({}, params);
		var fields = $('input[name],textarea[name]', f);
		fields.not('input:checkbox,input:radio').each(function()
		{
			p[this.getAttribute('name')] = this.value;
		});
		fields.filter('input:checkbox:checked,input:radio:checked').each(function()
		{
			if (!(this.getAttribute('name') in p))
			{
				p[this.getAttribute('name')] = [];
			}
			p[this.getAttribute('name')].push(this.value);
		});
		fields.filter('input:checkbox:not(:checked)').each(function()
		{
			if (!(this.getAttribute('name') in p))
			{
				p[this.getAttribute('name')] = [];
			}
			p[this.getAttribute('name')].push('');
		})
		$('select[name]', f).each(function()
		{
			var name = this.name;
			var pdata = [];
			$('option:selected', this).each(function()
			{
				pdata.push(this.value);

			});
			if (pdata.length > 0)
			{
				p[name] = pdata;
			}
		});
		return p;
	};
	
	return this.submit(function(e)
	{
		e.preventDefault();
		var p = getFormParams(this);
		var configurationArguments = {
			params: p,
			start: 0
		};
		if ('url' in args)
		{
			configurationArguments.url = args.url;
		}
		grid.grid_widgetConfigure(configurationArguments);
	});
};

$.fn.rowdblclick = function(f)
{
	this.bind('rowdblclick', f);
};

// automatic grids by class.

$(document).ready(function()
{
	$('div.data-grid').grid_widget();
});

})(jQuery);
