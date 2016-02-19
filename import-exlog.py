#!/usr/bin/env python3
# vim: syntax=python ts=4 et sw=4 sts=4:

import datetime
import sys


PercentageTable = [
    [100.00, 97.80, 95.50, 93.90, 92.20, 90.70, 89.20, 87.80], # 1 rep
    [95.50, 93.90, 92.20, 90.70, 89.20, 87.80, 86.30, 85.00], # 2 reps
    [92.20, 90.70, 89.20, 87.80, 86.30, 85.00, 83.70, 82.40], # 3 reps
    [89.20, 87.80, 86.30, 85.00, 83.70, 82.40, 81.10, 79.90], # 4 reps
    [86.30, 85.00, 83.70, 82.40, 81.10, 79.90, 78.60, 77.40], # 5 reps
    [83.70, 82.40, 81.10, 79.90, 78.60, 77.40, 76.20, 75.10], # 6 reps
    [81.10, 79.90, 78.60, 77.40, 76.20, 75.10, 73.90, 72.30], # 7 reps
    [78.60, 77.40, 76.20, 75.10, 73.90, 72.30, 70.70, 69.40], # 8 reps
]


def percentage(reps, rpe):
    if rpe == 10.0: return PercentageTable[reps - 1][0]
    if rpe == 9.5:  return PercentageTable[reps - 1][1]
    if rpe == 9.0:  return PercentageTable[reps - 1][2]
    if rpe == 8.5:  return PercentageTable[reps - 1][3]
    if rpe == 8.0:  return PercentageTable[reps - 1][4]
    if rpe == 7.5:  return PercentageTable[reps - 1][5]
    if rpe == 7.0:  return PercentageTable[reps - 1][6]
    if rpe == 6.5:  return PercentageTable[reps - 1][7]
    return 0.0


def calc_weight(e1rm, reps, rpe):
    # weight / percentage(reps, rpe) * 100 = e1rm
    # weight = e1rm / 100 * percentage(reps, rpe);
    return e1rm / 100 * percentage(reps, rpe)


#####################################################################


class Set:
    def __init__(self, weight, reps, rpe=0, failure=False):
        self.weight = float(weight)
        self.reps = int(reps)
        self.rpe = float(rpe)
        self.failure = bool(failure)

    def e1rm(self):
        factor = percentage(self.reps, self.rpe)

        # Use the Tuchscherer chart.
        if factor > 0:
            return self.weight / factor * 100

        # If RPEs are missing or the chart is inadequate, don't mislead.
        return 0.0

    # For cases that the RPE chart doesn't cover, we have the Wendler formula.
    def wendler(self):
        return self.weight + (self.weight * self.reps / 30)


class Lift:
    def __init__(self, name):
        self.name = name
        self.sets = []

    def addsets(self, slist):
        self.sets += slist

    # Get a list of non-warmup, actual training sets.
    def __get_heavysets(self):
        # Only include the top 20% of weights.
        topweight = max([0] + list(map(lambda x: x.weight, self.sets)))
        cutoff = topweight * 0.8
        return filter(lambda x: x.weight >= cutoff, self.sets)

    def e1rm(self):
        return max([0] + list(map(lambda x: x.e1rm(), self.__get_heavysets())))

    def wendler(self):
        return max([0] + list(map(lambda x: x.wendler(), self.__get_heavysets())))

    def volume(self):
        volume = 0
        for s in self.__get_heavysets():
            volume += s.reps
        return volume

    def tonnage(self):
        tonnage = 0
        for s in self.__get_heavysets():
            tonnage += (s.weight * s.reps)
        return tonnage


class TrainingSession:
    def __init__(self, year, month, day):
        self.date = datetime.date(year, month, day)
        self.bodyweight = 0.0
        self.lifts = []

    def setbodyweight(self, bodyweight):
        self.bodyweight = bodyweight

    def addlift(self, l):
        self.lifts.append(l)


#####################################################################


def from_kg(x):
    return float(x) * 2.20462262


def weight2float(x):
    # Used for chain notation.
    if "+" in x:
        sum = 0
        for k in x.split('+'):
            sum += weight2float(k)
        return sum

    if "kg" in x:
        return from_kg(x.replace("kg",""))
    return float(x)


def error(text):
    print("Error: " + text)
    sys.exit(1)


# Returns the number of 2-space tabs on the line.
def get_indentation_level(line):
    return (len(line) - len(line.lstrip())) >> 1


# Given text like "425x5x3" or "415x3@9", return a list of sets.
def makesets(text):
    xcount = text.count('x')

    # FIXME: For the moment, we'll just discard old pause notation.
    text = text.replace('p', '')
    # FIXME: Also some weirdo one-off "block" notation.
    text = text.replace('b', '')

    # If nothing special is noted, then it's probably a warmup set of 5.
    if xcount == 0:
        return [Set(weight2float(text), 5)]

    # Single set, maybe with RPE or failure.
    if xcount == 1 and not '(' in text:
        # Check for failure and remove it from the string.
        lowertext = text.lower()
        failure = 'f' in lowertext
        lowertext = lowertext.replace('f', '')

        # Check for RPE and remove it from the string.
        rpe = 0
        if '@' in lowertext:
            [lowertext, rpestr] = lowertext.split('@')
            rpe = float(rpestr)

        # Remaining string should just be weight x reps.
        [weight, reps] = lowertext.split('x')

        # Case of 200xf
        if not reps:
            reps = 0

        return [Set(weight2float(weight), int(reps), rpe, failure)]

    # Multiple sets with individual notation.
    # With failure: 225x(5,5,4f)
    # With RPE: 225x5@(7,8,9)
    if xcount == 1 and '(' in text:
        parens = text[text.index('(')+1 : -1].split(',')
        text = text[0 : text.index('(')]

        # List is across reps.
        if text[-1] == 'x':
            weight = text[0:-1]

            sets = []
            for k in parens:
                failure = 'f' in k
                reps = k.replace('f', '')
                sets.append(Set(float(weight), int(reps), 0, failure))
            return sets

        # List is across RPE.
        if text[-1] == '@':
            [weight, reps] = text[0:-1].split('x')
            return [Set(weight2float(weight), int(reps), float(x)) for x in parens]

    # Multiple sets across without RPE.
    # Failure is still sometimes denoted by "325x3fx3". Then all sets failed.
    if xcount == 2:
        failure = 'f' in text
        text = text.replace('f', '')

        [weight, reps, nsets] = text.split('x')
        return [Set(weight2float(weight), int(reps), 0, failure) for x in nsets]

    error("Could not parse sets: " + text)


def import_exlog(filename):

    # Open the file and remove all comments.
    with open(filename) as fd:
        lines = [x.split('#')[0].rstrip() for x in fd.readlines()]

    exlog = []

    # Zero'th level of indentation: dates.
    # First level of indentation: lift or bodyweight.
    # Second level of indentation: weights, reps, etc.

    session = None
    lift = None

    for line in lines:
        if len(line) == 0:
            continue

        level = get_indentation_level(line)

        # New training session.
        if level == 0:
            [year, month, day] = [int(x) for x in (line.split()[0]).split('-')]
            session = TrainingSession(year, month, day)
            exlog.append(session)

        # New lift for the current session, or bodyweight declaration.
        elif level == 1:
            name = line.lstrip().split(':')[0]
            if name == "weight":
                maybeweight = line.split(':')[1].strip()
                if maybeweight:
                    session.setbodyweight(float(maybeweight))

            # The earliest entries do some jogging for warmup.
            elif name == "warmup":
                continue

            else:
                lift = Lift(name)
                session.addlift(lift)

        # List of sets for the current lift.
        elif level == 2:
            # Can't just split by comma, since a line may be "155x3, 175x(2,2,1)".
            for x in line.split(', '):
                sets = makesets(x.strip())
                lift.addsets(sets)
            
    return exlog


if __name__ == '__main__':
    import sys
    exlog = import_exlog(sys.argv[1])

    for session in exlog:
        for lift in session.lifts:
            print(lift.name + " " + str(lift.e1rm()))
