(function($)
{

var createTree = function(args)
{
	var $self = this;

	var nodeSelected = function(itm)
	{
		$self.trigger('nodeselected', [itm]);
	};

	var nodeDblClick = function(itm)
	{
		$self.trigger('nodedblclick', [itm]);
	};

	var Node = function(data)
	{
		var isFolder = data.isFolder;
		var self = this;
		var items = null;

		var div = $([
			'<div class="tree-widget-node collapsed">',
				'<div class="tree-widget-item-state">',
				(isFolder ?
					['<a class="collapsed" href="javascript:;" title="', $.fn.tree_widget.locale.folderExpandHint, '">&nbsp;</a>'].join('')
					: ''),
				'</div>',
				'<div class="tree-widget-item-icon ', (isFolder ? 'icon-collapsed tree-widget-folder' : 'tree-widget-leaf'),'" title="', (isFolder ? $.fn.tree_widget.locale.folderTitle : $.fn.tree_widget.locale.leafTitle), '"></div>',
				'<div class="tree-widget-text">', data.text, '</div>',
			'</div>',
			''].join(''));
		div.data('node', this);
		if ('hint' in data)
		{
			div.attr('title', data.hint);
		}

		var isCollapsed = function()
		{
			return div.hasClass('collapsed');
		};

		var isExpanded = function()
		{
			return div.hasClass('expanded');
		};

		var isLoading = function()
		{
			return div.children('tree-widget-item-icon').hasClass('loading');
		};

		var getParent = function()
		{
			if (!div.parent().hasClass('tree-widget-node-children'))
			{
				return null;
			}
			return div.parents('div.tree-widget-node').eq(0).data('node');
		};

		var internalExpand = function()
		{
			div.removeClass('collapsed').addClass('expanded');
			div.children('div.tree-widget-item-icon').removeClass('icon-collapsed').addClass('icon-expanded');
			$('>div.tree-widget-item-state>a', div).removeClass('collapsed').addClass('expanded');
			div.children('div.tree-widget-node-children').show(args.animationSpeed);
		};

		var loaded = function(childrenData)
		{
			items = childrenData.items;
			div.children('div.tree-widget-item-icon').removeClass('loading');
			if (items.length > 0)
			{
				var childrenDiv = $('<div class="tree-widget-node-children" style="display: none;"></div>').appendTo(div);
				for (var i = 0; i < items.length; i++)
				{
					var node = new Node(items[i]);
					node.renderTo(childrenDiv);
				}
			}
			internalExpand();
		};

		var beforeLoad = function()
		{
			div.removeClass('collapsed');
			div.children('div.tree-widget-item-icon').removeClass('icon-collapsed').addClass('loading');
		};

		var loadItems = function()
		{
			loaded(data);
		};

		var load = function()
		{
			var url = args.url;
			var params = $.extend({}, args.params, { parent: data.id });
			if ('url' in data)
			{
				url = data.url;
			}
			if ('params' in data)
			{
				params = $.extend(params, data.params);
			}
			$.getJSON(
				url, 
				params, 
				loaded
				);
		};

		this.renderTo = function(parentDiv)
		{
			div.appendTo(parentDiv);
			return this;
		};

		this.expand = function()
		{
			if (items == null)
			{
				beforeLoad();
				if ('items' in data)
				{
					loadItems();
				}
				else
				{
					load();
				}
			}
			else
			{
				internalExpand();
			}
			return this;
		};

		this.collapse = function()
		{
			div.children('div.tree-widget-node-children').hide(args.animationSpeed);
			div.addClass('collapsed').removeClass('expanded');
			$('>div.tree-widget-item-state>a', div).addClass('collapsed').removeClass('expanded');
			div.children('div.tree-widget-item-icon').addClass('icon-collapsed').removeClass('icon-expanded');
			return this;
		};

		var toggle = function()
		{
			if (isLoading())
			{
				return;
			}
			if (isExpanded()) 
			{
				self.collapse();
			}
			else 
			{
				self.expand();
			}
		};

		var selectMe = function()
		{
			var treeView = div.parents('.tree-widget-view').eq(0);
			$('div.tree-widget-icon, div.tree-widget-state, div.tree-widget-text', treeView).removeClass('tree-widget-selected');
			$('>div.tree-widget-icon, >div.tree-widget-state, >div.tree-widget-text', div).addClass('tree-widget-selected');
			div.focus();
			nodeSelected({node: self, data: data});
		};

		var selectParent = function()
		{
			var p = getParent();
			if (p != null)
			{
				p.select();
			}
		};

		var dblclickMe = function()
		{
			selectMe();
			nodeDblClick({node: self, data: data});
		};

		this.select = function()
		{
			selectMe();
			return this;
		};

		$('>div.tree-widget-item-state>a', div).click(toggle);
		div.children('div.tree-widget-folder').dblclick(toggle);
		div.children('div.tree-widget-text').click(selectMe).dblclick(dblclickMe);
	};

	var rootArgs = {id: '', isFolder: true, text: args.rootText};
	if ('items' in args)
	{
		rootArgs.items = args.items;
	}
	var root = new Node(rootArgs);
	this.addClass('tree-widget-view');
	root.renderTo(this).expand();
};

$.fn.tree_widget = function(args)
{
	if (args == null)
	{
		args = {};
	}
	args = $.extend({}, $.fn.tree_widget.defaults, args);
	this.each(function()
	{
		var concreteArgs = {};
		var $this = $(this);
		if ($this.text() != '' && $this.text().charAt(0) == '{')
		{
			concreteArgs = eval('(' + $this.text() + ')');
		}
		$this.empty();
		concreteArgs = $.extend({}, args, concreteArgs);
		createTree.call($this, concreteArgs);
	});
	return this;
};

$.fn.tree_widget.defaults = {
	params: {},
	rootText: 'Root',
	animationSpeed: 'fast'
	};

$.fn.tree_widget.locale = {
	folderCollapseHint: 'Click to collapse',
	folderExpandHint: 'Click to expand',
	folderTitle: 'Folder',
	leafTitle: 'Leaf'
	};

$.fn.nodeselected = function(f)
{
	return this.bind('nodeselected', f);
};

$.fn.nodedblclick = function(f)
{
	return this.bind('nodedblclick', f);
};

$(document).ready(function()
{
	$('div.tree-widget').tree_widget();
});

})(jQuery);
