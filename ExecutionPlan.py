import time
import json

class ExecutionPlan(object):

    def __init__(self):
        self.plan_as_dict_array = []
        self.started_list = []
        self.completed_list = []

    """ constructor-like function for building plan from dict array
    """
    def from_dict_array(self, d):
        self.plan_as_dict_array = [x.copy() for x in d]  # create a copy of dict array
        return self

    """ constructor-like function for building plan from formatted string
    """
    def from_tree_string(self, tree_string):
        def extract_name(s):
            return s.replace('\t', '')

        def turn_line_to_dict(i, lines, parents_stack):
            indent_level = lines[i].count("\t")

            prev_indent_level = 0
            if i > 0:
                prev_indent_level = lines[i-1].count("\t")

            if indent_level == prev_indent_level + 1:
                parents_stack.append(extract_name(lines[i - 1]))
            elif indent_level == prev_indent_level - 1:
                parents_stack.pop()
            elif indent_level > prev_indent_level + 1 or indent_level < prev_indent_level - 1:
                raise ValueError("Invalid indentation for line {}".format(line))

            return {"name": extract_name(lines[i]), "dependency": parents_stack[-1]}  # dependency will be the last parent

        parents_stack = [None]
        lines = tree_string.split('\n')
        self.plan_as_dict_array = list(map(lambda l: turn_line_to_dict(l, lines, parents_stack), range(0, len(lines))))

        return self

    def is_incomplete(self):
        return len(self.plan_as_dict_array) != len(self.completed_list)

    def is_task_complete(self, index):
        return index in self.completed_list

    def is_ready(self, index=None, name=None):
        task = None
        if index is not None:
            task = self.plan_as_dict_array[index]
        elif name is not None:
            task = [x for x in self.plan_as_dict_array if x['name'] == name][0]
            index = self.plan_as_dict_array.index(task)

        if self.plan_as_dict_array.index(task) in self.completed_tasks():
            return False
        if task['dependency'] is None:
            is_dependency_complete = True
        else:
            is_dependency_complete = self.is_task_complete(index=[i for i in range(0, len(self.plan_as_dict_array)) if self.plan_as_dict_array[i]['name'] == task['dependency']][0])
        return is_dependency_complete and not self.is_task_complete(index=index) and not self.is_task_started(index=index)

    def is_task_started(self, index=None):
        return index in self.started_list

    def ready_tasks(self):
        return [i for i in range(0, len(self.plan_as_dict_array)) if self.is_ready(index=i)]

    def completed_tasks(self):
        return [self.plan_as_dict_array[i] for i in self.completed_list]

    def mark_started(self, index):
        if self.is_ready(index=index):
            self.started_list.append(index)
            self.plan_as_dict_array[index]['start_time'] = time.time()
        else:
            raise ValueError("Task is not ready to start")

    def mark_completed(self, index):
        if self.is_task_started(index=index):
            self.completed_list.append(index)
            self.plan_as_dict_array[index]['end_time'] = time.time()
        else:
            raise ValueError("Task cannot be completed before starting")

    def get_dependants(self, i):
        return [self.plan_as_dict_array.index(j) for j in self.plan_as_dict_array if
                j['dependency'] == self.plan_as_dict_array[i]['name']]

    def __str__(self):
        def stringify_item_with_dependencies(i, visited_list, indent_level, accum):
            if i in visited_list:
                return accum
            else:
                visited_list.append(i)
                indentation = "".join(["\t" for x in range(0, indent_level)])
                readiness = ""
                completion = ""
                started = ""
                if self.is_ready(index=i):
                    readiness = " Ready "
                if self.is_task_complete(index=i):
                    completion = " Completed "
                if self.is_task_started(index=i):
                    started = " Started "
                str_this_item = indentation + self.plan_as_dict_array[i]['name'] + readiness + started + completion + "\n"
                str_dependents = "".join([stringify_item_with_dependencies(j, visited_list, indent_level + 1, accum) for j in self.get_dependants(i)])
                return accum + str_this_item + str_dependents

        visited_list = []  # passing visited list in param as lists are passed by reference in python; TODO: refactor and find a better way
        return "".join([stringify_item_with_dependencies(i, visited_list, 0, "") for i in range(0, len(self.plan_as_dict_array))])

    def as_json(self):
        return json.dumps(self.plan_as_dict_array, indent=4, separators=(',', ': '))

    def as_gantt(self, resolution=100.0):
        if self.is_incomplete():
            return "Not implemented for incomplete plans"
        else:
            time_range_start = self.plan_as_dict_array[0]['start_time']
            time_range_end = self.plan_as_dict_array[0]['end_time']
            biggest_name_size = len(self.plan_as_dict_array[0]['name'])

            for task in self.plan_as_dict_array:
                if task['start_time'] < time_range_start:
                    time_range_start = task['start_time']
                if task['end_time'] > time_range_end:
                    time_range_end = task['end_time']
                if len(task['name']) > biggest_name_size:
                    biggest_name_size = len(task['name'])

            time_step = (time_range_end - time_range_start) / resolution

            def n_chars(c, n):
                return "".join(list(map(lambda x: c, range(0, int(n)))))

            gantt_str = "".ljust(biggest_name_size+1) + n_chars(".",(time_range_end-time_range_start)/time_step)+"\n"
            for task in self.plan_as_dict_array:
                name_padded = task['name'].ljust(biggest_name_size+1)
                prefix = n_chars(" ", (task['start_time']-time_range_start)/time_step)
                actual = n_chars(".", (task['end_time']-task['start_time'])/time_step)
                gantt_str += name_padded + prefix + actual + "\n"

            return gantt_str
