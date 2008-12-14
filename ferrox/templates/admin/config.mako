<%namespace name="lib" file="/lib.mako"/>
<%inherit file="base.mako" />

<%def name="isadmin()">
	% if not c.auth_user.can('admin.config_admin'):
		style="display: none;"
	% endif
</%def>                       

<link rel="stylesheet" type="text/css" href="/stylesheets/grid_widget.css" />
<link rel="stylesheet" type="text/css" href="/stylesheets/tree_widget.css" />
<style type="text/css">
#value-list
{
	padding: 4px;
	border: 1px solid #eee;
}

#value-list.disabled-value-list, .readonly
{
	background-color: #f2f2f2;
}

#value-list.loading-value-list
{
	background: #f8f8f8 url('/images/m.tree/loading.gif') center center no-repeat;
}

#mess-area
{
	background-color: $fee;
	border: 1px solid #f00;
	padding: 2px;
	margin: 2px;
}
</style>
<script src="/javascripts/grid_widget.js" type="text/javascript"></script>
<script src="/javascripts/tree_widget.js" type="text/javascript"></script>
<script src="/javascripts/grid_widget_en.js" type="text/javascript"></script>
<script src="/javascripts/tree_widget_en.js" type="text/javascript"></script>
<script type="text/javascript">
(function($)
{

var editVar = function(data)
{
        for (var n in data)
        {
		if(n == 'value' && data.type == 3)
		{
			var values = data.value.split(/,/);
			for(var n in values)
			{
				$('#option_' + values[n]).attr('selected', 'selected');
			}
		}
		else
		{
	                $('#var_' + n).val(data[n]);
		}
                $('#var_old_' + n).val(data[n]);
        }
        if ($('#var_comment').val() == '')
        {
                $('#var_comment').removeAttr('readonly').removeClass('readonly').parent().prev().attr('checked', 'checked');
        }
        $('#var-form').show();
        $('#var_value').focus();
};

$.fn.grid_widget.renderers.var_name = function(v, e)
{
	% if c.auth_user.can('admin.config_edit'):
        var r = $([
                '<a href="javascript:;">',
                v,
                '</a>',
                ''].join(''));

        r.click(function()
        {
		var regexp = $('<textarea id="var_value" style="width: 98%;"></textarea>');
		var list = $('<select id="var_value"></select>');
		var multilist = $('<select id="var_value" multiple="multiple" size="10"></select>');

		switch(e.rowData[2])
		{
		case 1:
			$('#value').empty().append(regexp);
			break;
		case 2:
			$('#value').empty().append(list);
			break;
		case 3:
			$('#value').empty().append(multilist);
			break;
		default:
			$('#value').empty().append(regexp);
		}
		if((e.rowData[2] == 2) || (e.rowData[2] == 3))
		{
			try
			{
				data = eval('(' + e.rowData[3] + ')');
				for(var n in data)
				{
					$('#var_value').append('<option id="option_'+n+'" value='+n+'>'+data[n]+'</option>');
				}
			}
			catch(err)
			{
				$('#value').empty().append(regexp).attr('readonly', 'readonly').append('<font style="color: red;">Error in pattern!</font>');
			}
		}
                editVar({
                        id: e.rowData[0],
                        section: e.rowData[1],
			type: e.rowData[2],
			pattern: e.rowData[3],
                        name: e.rowData[7],
                        value: e.rowData[8],
                        comment: e.rowData[9],
                        });
        });
	% else:
	var r = v;
	% endif
        return r;
};

$.fn.grid_widget.renderers.var_value = function(v, e)
{
	var r, data;
	if((e.rowData[2] == 2) || (e.rowData[2] == 3))
	{
		try
		{
			data = eval('(' + e.rowData[3] + ')');
		}
		catch(err)
		{
			data = null;
		}
	}
	switch(e.rowData[2])
	{
	case 1:
		r = v;
		break;
	case 2:
		if(data != null)
		{
			r = data[v];
		}
		break;
	case 3:
		if(data != null)
		{
			var a = new Array();
			var s = v.split(/,/);
			for(var n in s)
			{
				a.push(data[s[n]]);
			}
			r = a.join(", ");
		}
		break;
	default:
		r = v;
	}

	return r;
};

var dropSectionValues = function()
{
        $('#section-title').text('');
        $('#value-list')
                .addClass('disabled-value-list').removeClass('loading-value-list')
                .grid_widgetConfigure({url: '${h.url_for(controller='admin', action='config_ajax')}', params: {action: 'empty_list'}})
                ;
        $('#var-form').hide();
};

var loadSectionValues = function(data)
{
        $('#section-title').text(data.section);
        $('#value-list')
                .removeClass('disabled-value-list').addClass('loading-value-list')
                .grid_widgetConfigure({url: '${h.url_for(controller='admin', action='config_ajax')}', params: {action: 'get_values', section: data.section}})
                ;
        $('#var_section').val(data.section);
        $('#var_old_section').val(data.section);
        $('#var-form').hide();
};

var nodeSelected = function(e, ex)
{
        if ('section' in ex.data)
        {
                loadSectionValues(ex.data);
        }
        else
        {
                dropSectionValues();
        }
};

$(document).ready(function()
{
        $('#cplace')
                .tree_widget({
                        url: '${h.url_for(controller='admin', action='config_ajax')}',
                        params: {
                                action: 'get_tree'
                                },
                        rootText: 'Ferrox configuration'
                        })
                .nodeselected(nodeSelected)
                ;
        $('input:text,textarea,select', $('#var-form')).val('');
        $('#var-form>input:checkbox').removeAttr('checked').attr('title', 'Allow change value').click(function()
        {
                var $this = $(this);
                var el = $('input, textarea', $this.next()).focus().select();
                if ($this.attr('checked'))
                {
                        el.removeAttr('readonly').removeClass('readonly');
                }
                else
                {
                        el.attr('readonly', 'readonly').addClass('readonly');
                }
		var el = $('select', $this.next()).focus().select();
                if ($this.attr('checked'))
                {
                        el.removeAttr('disabled').removeClass('readonly');
                }
                else
                {
                        el.attr('disabled', 'disabled').addClass('readonly');
                }
        });

        var psnOk = function()
        {
                if ($.trim($('#var_section').val()) == '')
                {
                        alert('Section name can\'t be empty');
                        return false;
                }
                if ($.trim($('#var_name').val()) == '')
                {
                        alert('Variable name can\'t be empty');
                        return false;
                }
                if ($.trim($('#var_comment').val()) == '')
                {
                        alert('Comment can\'t be empty');
                        return false;
                }
		if ($.trim($('#var_type').val()) == 1)
		{
			var regexp = new RegExp($.trim($('#var_pattern').val()));
			if(!regexp.test($.trim($('#var_value').val())))
			{
				alert('Value not suitable with this pattern');
				$('#var_value').focus();
				return false;
			}
		}
                return true;
        };

        var refreshValues = function(html)
        {
                $('#mess-area').html(html).css('display', (html != 'done') ? '' : 'none');
                $('#value-list').grid_widgetRefresh();
        };

        $('#var-form').submit(function(e)
        {
                e.preventDefault();
                if (!psnOk())
                {
                        return;
                }
                $('#var-form').hide();
		var var_value = $('#var_value').val();
		if($('#var_type').val() == 3)
		{
			var a = new Array();
			$('[id*=option_]').each(
				function(intIndex)
				{
					if($(this).attr('selected'))
					{
						a.push($(this).val());
					}
				}
			);
			var_value = a.join(",");
		}
                $.post('${h.url_for(controller='admin', action='config')}', {
                                action: 'save',
                                old_section: $('#var_old_section').val(),
                                old_name: $('#var_old_name').val(),
				old_type: $('#var_old_type').val(),
				old_pattern: $('#var_old_pattern').val(),
				old_comment: $('#var_old_comment').val(),
                                section: $('#var_section').val(),
                                name: $('#var_name').val(),
				type: $('#var_type').val(),
				pattern: $('#var_pattern').val(),
                                value: var_value,
                                comment: $('#var_comment').val(),
                        }, refreshValues);
        });
});

})(jQuery);
</script>

<table style="width: 100%; background: inherit;"><tbody>
	<tr style="height: 50%;">
		<td rowspan="2" id="cplace" style="width: 300px;">
		</td>
		<td id="vlistplace">
			<div>List of &laquo;<b id="section-title"></b>&raquo; variables</div>
			<div id="value-list" class="data-grid">{url: '${h.url_for(controller='admin', action='config_ajax')}', limit: 20, params: {action: 'empty_list'}, cvs: true}</div>
		</td>
	</tr>
	<tr>
		<td id="vplace">
			<div id="mess-area" style="display: none;"></div>
			<form id="var-form" method="POST" style="display: none; padding: 1%;">
				<input type="hidden" id="var_old_section" value="" />
				<input type="hidden" id="var_old_name" value="" />
				<input type="hidden" id="var_old_type" value="" />
				<input type="hidden" id="var_old_pattern" value="" />
				<input type="hidden" id="var_old_comment" value="" />
				<input type="checkbox" ${self.isadmin()} />
				<label ${self.isadmin()} >Section:<br />
					<input type="text" id="var_section" value="" readonly="readonly" class="readonly" maxlength="32" />
				</label><br ${self.isadmin()} />
				<input type="checkbox" ${self.isadmin()} />
				<label ${self.isadmin()} >Variable name:<br />
					<input type="text" id="var_name" value="" readonly="readonly" class="readonly" maxlength="32" autocomplete="off" />
				</label><br ${self.isadmin()} />
				<input type="checkbox" ${self.isadmin()} />
				<label ${self.isadmin()} >Type:<br />
					<select id="var_type" disabled="disabled" class="readonly" value="">
						<option value="1">Regexp</option>
						<option value="2">List</option>
						<option value="3">MultiList</option>
					</select>
				</label><br ${self.isadmin()} />
				<input type="checkbox" ${self.isadmin()} />
				<label ${self.isadmin()} >Pattern:<br />
					<textarea readonly="readonly" class="readonly" id="var_pattern" style="width: 98%;"></textarea>
				</label><br ${self.isadmin()} />
				<label>Variable value:<br />
					<div id="value">
					</div>
				</label><br />
				<input type="checkbox" ${self.isadmin()} />
				<label ${self.isadmin()} >Comment:<br />
					<textarea readonly="readonly" class="readonly" id="var_comment" style="width: 98%;"></textarea>
				</label><br ${self.isadmin()} />
				<input type="submit" value="Save" />
			</form>
		</td>
	</tr>
</tbody></table>

<%def name="title()">Edit config</%def>
